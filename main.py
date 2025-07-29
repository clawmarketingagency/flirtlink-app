# FLIRTLINK AI AGENT PLATFORM - PRODUCTION READY
# Backend: FastAPI + GPT-4 Turbo + Supabase (Optimized for Railway Deployment)

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

# === Load Environment Variables ===
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_DB_USER = os.getenv("SUPABASE_DB_USER")
SUPABASE_DB_PASS = os.getenv("SUPABASE_DB_PASS")
SUPABASE_DB_NAME = os.getenv("SUPABASE_DB_NAME")

# === FastAPI Initialization ===
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === PostgreSQL DB Connection ===
async def get_db():
    parsed_url = urlparse(SUPABASE_DB_URL)
    conn = await asyncpg.connect(
        user=SUPABASE_DB_USER,
        password=SUPABASE_DB_PASS,
        database=SUPABASE_DB_NAME,
        host=parsed_url.hostname,
        port=parsed_url.port or 5432
    )
    try:
        yield conn
    finally:
        await conn.close()

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
        raise HTTPException(status_code=500, detail=f"DB Insert Error: {str(e)}")

@app.post("/chat")
async def chat_with_agent(req: ChatRequest, db=Depends(get_db)):
    row = await db.fetchrow("SELECT prompt, links FROM agents WHERE id = $1", req.agent_id)
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")

    personality = row['prompt']
    links = row['links']

    prompt = f"""
You are a flirty, naughty, teasing AI assistant for an OnlyFans creator.
Always stay in character and be suggestive, seductive, and playful.

Personality:
{personality}

Chat:
User: {req.user_input}
Agent:"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        reply = response.choices[0].message['content']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")

    return {"reply": reply.strip(), "links": links}

@app.get("/agent/{agent_id}")
async def get_agent(agent_id: str, db=Depends(get_db)):
    row = await db.fetchrow("SELECT persona_name, prompt, links FROM agents WHERE id = $1", agent_id)
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        "persona_name": row['persona_name'],
        "prompt": row['prompt'],
        "links": row['links']
    }

