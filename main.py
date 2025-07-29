# FLIRTLINK AI AGENT PLATFORM - CLEANED FOR DEPLOYMENT
# Backend: FastAPI + GPT-4 Turbo + Supabase (Pages Router Compatible)

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import uuid
import os
import json
import asyncpg
from dotenv import load_dotenv

# === Load environment variables ===
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_DB_USER = os.getenv("SUPABASE_DB_USER")
SUPABASE_DB_PASS = os.getenv("SUPABASE_DB_PASS")
SUPABASE_DB_NAME = os.getenv("SUPABASE_DB_NAME")

# === FastAPI App Setup ===
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Database Connection ===
async def get_db():
    parsed_host = SUPABASE_DB_URL.split("//")[-1].split(":")[0]
    conn = await asyncpg.connect(
        user=SUPABASE_DB_USER,
        password=SUPABASE_DB_PASS,
        database=SUPABASE_DB_NAME,
        host=parsed_host
    )
    try:
        yield conn
    finally:
        await conn.close()

# === Request & Response Models ===
class AgentInit(BaseModel):
    creator_id: str
    persona_name: str
    personality_prompt: str
    links: dict

class ChatRequest(BaseModel):
    agent_id: str
    user_input: str

class CreateAgentResponse(BaseModel):
    agent_id: str

# === Routes ===
@app.post("/create-agent", response_model=CreateAgentResponse)
async def create_agent(agent: AgentInit, db=Depends(get_db)):
    agent_id = str(uuid.uuid4())
    await db.execute("""
        INSERT INTO agents (id, creator_id, persona_name, prompt, links)
        VALUES ($1, $2, $3, $4, $5)
    """, agent_id, agent.creator_id, agent.persona_name, agent.personality_prompt, json.dumps(agent.links))
    return {"agent_id": agent_id}

@app.post("/chat")
async def chat_with_agent(req: ChatRequest, db=Depends(get_db)):
    row = await db.fetchrow("SELECT prompt, links FROM agents WHERE id = $1", req.agent_id)
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")

    personality = row['prompt']
    links = row['links']

    prompt = f"""
You are a flirty, naughty AI OnlyFans agent.
Stay in character, respond sexually and teasingly based on this personality:

Personality:
{personality}

Chat:
User: {req.user_input}
Agent:"""

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )
    reply = response.choices[0].message['content']

    return {"reply": reply, "links": links}

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

# === SQL SCHEMA (run once in Supabase) ===
# CREATE TABLE agents (
#   id UUID PRIMARY KEY,
#   creator_id TEXT,
#   persona_name TEXT,
#   prompt TEXT,
#   links JSONB
# );

# === .env Example ===
# OPENAI_API_KEY=sk-...
# SUPABASE_DB_URL=postgresql://dbhost:5432/dbname
# SUPABASE_DB_USER=postgres
# SUPABASE_DB_PASS=yourpassword
# SUPABASE_DB_NAME=postgres
