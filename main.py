# FLIRTLINK AI AGENT PLATFORM - IMPROVED VERSION
# Backend: FastAPI + GPT-4 Turbo + Supabase + Connection Pooling

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from urllib.parse import urlparse
import openai
import asyncpg
import uuid
import os
import json
import logging

# === Load Environment Variables ===
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_DB_USER = os.getenv("SUPABASE_DB_USER")
SUPABASE_DB_PASS = os.getenv("SUPABASE_DB_PASS")
SUPABASE_DB_NAME = os.getenv("SUPABASE_DB_NAME")

# === Logging Configuration ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === FastAPI App Initialization ===
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # WARNING: In production, restrict this to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === PostgreSQL Connection Pool ===
class Database:
    pool: asyncpg.pool.Pool = None

db_instance = Database()

@app.on_event("startup")
async def startup():
    parsed_url = urlparse(SUPABASE_DB_URL)
    db_instance.pool = await asyncpg.create_pool(
        user=SUPABASE_DB_USER,
        password=SUPABASE_DB_PASS,
        database=SUPABASE_DB_NAME,
        host=parsed_url.hostname,
        port=parsed_url.port or 5432,
        min_size=1,
        max_size=5
    )
    logger.info("Connected to the database.")

@app.on_event("shutdown")
async def shutdown():
    await db_instance.pool.close()
    logger.info("Database connection closed.")

async def get_db():
    async with db_instance.pool.acquire() as connection:
        yield connection

# === Models ===
class AgentInit(BaseModel):
    creator_id: str
    persona_name: str
    personality_prompt: str
    links: dict  # Example: {"onlyfans": "https://...", "tip": "https://..."}

class ChatRequest(BaseModel):
    agent_id: str
    user_input: str

class CreateAgentResponse(BaseModel):
    agent_id: str

# === Routes ===
@app.post("/create-agent", response_model=CreateAgentResponse)
async def create_agent(agent: AgentInit, db=Depends(get_db)):
    agent_id = str(uuid.uuid4())
    try:
        await db.execute("""
            INSERT INTO agents (id, creator_id, persona_name, prompt, links)
            VALUES ($1, $2, $3, $4, $5)
        """, agent_id, agent.creator_id, agent.persona_name, agent.personality_prompt, json.dumps(agent.links))
        return {"agent_id": agent_id}
    except Exception as e:
        logger.error(f"Error inserting agent: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while creating agent.")

@app.post("/chat")
async def chat_with_agent(req: ChatRequest, db=Depends(get_db)):
    try:
        row = await db.fetchrow("SELECT prompt, links FROM agents WHERE id = $1", req.agent_id)
        if not row:
            raise HTTPException(status_code=404, detail="Agent not found")

        personality = row["prompt"]
        links = row["links"]

        system_prompt = f"""
You are a flirty, naughty, teasing AI assistant for an OnlyFans creator.
Stay in character. Be suggestive, seductive, fun, and emotionally engaging.

Personality:
{personality}

Now respond in character to:
User: {req.user_input}
Agent:
        """

        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": system_prompt}],
            max_tokens=300,
            temperature=0.9
        )
        reply = response.choices[0].message["content"].strip()
        return {"reply": reply, "links": links}
    except openai.error.OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise HTTPException(status_code=500, detail="OpenAI API error.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error during chat.")

@app.get("/agent/{agent_id}")
async def get_agent(agent_id: str, db=Depends(get_db)):
    try:
        row = await db.fetchrow("SELECT persona_name, prompt, links FROM agents WHERE id = $1", agent_id)
        if not row:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {
            "persona_name": row["persona_name"],
            "prompt": row["prompt"],
            "links": row["links"]
        }
    except Exception as e:
        logger.error(f"Error fetching agent: {e}")
        raise HTTPException(status_code=500, detail="Error fetching agent data.")
