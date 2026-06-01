from typing import Dict, Any
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger


CHATBOT_SYSTEM_PROMPT = """You are a helpful assistant for students in an AI bootcamp.
Answer questions about course deadlines, materials, lab instructions, and assignments.
Be concise and helpful. Answer in Vietnamese.
If you don't have specific information (like exact deadlines or URLs), say so honestly
instead of making up details."""


class Chatbot:
    """
    Baseline chatbot — không có tools, gọi LLM trực tiếp.
    Dùng để so sánh với ReActAgent trong evaluation.
    """

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def run(self, user_input: str) -> Dict[str, Any]:
        logger.log_event("CHATBOT_START", {"input": user_input, "model": self.llm.model_name})

        result = self.llm.generate(user_input, system_prompt=CHATBOT_SYSTEM_PROMPT)

        logger.log_event("CHATBOT_END", {
            "latency_ms": result["latency_ms"],
            "total_tokens": result["usage"].get("total_tokens", 0),
        })

        return {
            "answer": result["content"],
            "trace": [],
            "metrics": {
                "steps": 1,
                "total_tokens": result["usage"].get("total_tokens", 0),
                "latency_ms": result["latency_ms"],
            },
        }
