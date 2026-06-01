import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from src.core.openai_provider import OpenAIProvider
from src.agent.agent import ReActAgent
from src.tools.discord_tool import TOOL_SPEC as DISCORD_TOOL
from src.tools.pdf_tool import TOOL_SPEC as PDF_TOOL
from src.tools.github_tool import TOOL_SPEC as GITHUB_TOOL
from src.tools.lms_tool import TOOL_SPEC as LMS_TOOL
from src.tools.drive_tool import TOOL_SPEC as DRIVE_TOOL
from chatbot import Chatbot

app = FastAPI(
    title="Student Knowledge Agent",
    description="AI Agent giúp sinh viên tìm thông tin môn học từ Discord, PDF, GitHub, LMS, Drive",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM provider (OpenAI)
llm = OpenAIProvider(
    model_name=os.getenv("DEFAULT_MODEL", "gpt-4o"),
    api_key=os.getenv("OPENAI_API_KEY"),
)

# Tất cả 5 tools
TOOLS = [DISCORD_TOOL, PDF_TOOL, GITHUB_TOOL, LMS_TOOL, DRIVE_TOOL]

# Initialize agent và chatbot baseline
agent = ReActAgent(llm=llm, tools=TOOLS, max_steps=int(os.getenv("MAX_STEPS", 5)))
chatbot = Chatbot(llm=llm)


class ChatRequest(BaseModel):
    message: str
    mode: str = "agent"  # "agent" or "chatbot"


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Endpoint chính: nhận câu hỏi, trả lời qua Agent hoặc Chatbot.
    - mode=agent  → ReAct loop với 5 tools
    - mode=chatbot → LLM trực tiếp, không tools
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if request.mode == "chatbot":
        result = chatbot.run(request.message)
    elif request.mode == "agent":
        result = agent.run(request.message)
    else:
        raise HTTPException(status_code=400, detail="mode must be 'agent' or 'chatbot'")

    return {
        "answer": result["answer"],
        "mode": request.mode,
        "trace": result.get("trace", []),
        "metrics": result.get("metrics", {}),
    }


@app.get("/health")
async def health():
    """Health check — kiểm tra server và danh sách tools."""
    return {
        "status": "ok",
        "provider": os.getenv("DEFAULT_PROVIDER", "openai"),
        "model": os.getenv("DEFAULT_MODEL", "gpt-4o"),
        "tools": [t["name"] for t in TOOLS],
        "max_steps": int(os.getenv("MAX_STEPS", 5)),
    }
