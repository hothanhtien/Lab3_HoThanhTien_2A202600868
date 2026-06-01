import re
import os
from typing import List, Dict, Any
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger


class ReActAgent:
    """
    ReAct-style Agent: Thought → Action → Observation loop.
    Kế thừa skeleton từ Lab3, implement đầy đủ run() và _execute_tool().
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = {t["name"]: t for t in tools}
        self.max_steps = max_steps

    def get_system_prompt(self) -> str:
        """
        System prompt hướng dẫn agent theo ReAct format.
        Bao gồm danh sách tools và format Thought/Action/Observation.
        """
        tool_descriptions = "\n".join(
            [f"- {name}: {spec['description']}" for name, spec in self.tools.items()]
        )
        return f"""You are a helpful assistant for students in an AI bootcamp course.
You have access to the following tools to find accurate course information:

{tool_descriptions}

Use EXACTLY this format for every response until you reach a Final Answer:

Thought: <your reasoning about what information you need and which tool to use>
Action: <tool_name>("<search query>")

When you have enough information to answer completely, respond with:

Thought: I now have enough information to answer the student's question.
Final Answer: <your complete, helpful answer in Vietnamese>

Rules:
- Always start your response with "Thought:"
- Action format must be exactly: tool_name("query") — use double quotes
- Call only ONE action per response turn
- After each Observation, write a new Thought before the next Action
- Do NOT fabricate information — only use facts from tool Observations
- Answer in Vietnamese, be concise and helpful
"""

    def run(self, user_input: str) -> Dict[str, Any]:
        """
        Thực thi ReAct loop:
        1. Generate LLM response (Thought + Action)
        2. Parse Action → execute tool → get Observation
        3. Append Observation to context → repeat
        4. Stop when Final Answer found or max_steps reached
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        trace = []
        conversation = f"Student question: {user_input}\n"
        total_tokens = 0
        total_latency = 0

        for step in range(1, self.max_steps + 1):
            result = self.llm.generate(conversation, system_prompt=self.get_system_prompt())
            llm_output = result["content"]
            total_tokens += result["usage"].get("total_tokens", 0)
            total_latency += result["latency_ms"]

            # Check for Final Answer
            if "Final Answer:" in llm_output:
                final_answer = llm_output.split("Final Answer:")[-1].strip()
                logger.log_event("AGENT_END", {
                    "steps": step,
                    "total_tokens": total_tokens,
                    "total_latency_ms": total_latency,
                    "status": "success",
                })
                return {
                    "answer": final_answer,
                    "trace": trace,
                    "metrics": {
                        "steps": step,
                        "total_tokens": total_tokens,
                        "latency_ms": total_latency,
                    },
                }

            # Parse Thought
            thought_match = re.search(
                r"Thought:\s*(.+?)(?=Action:|Final Answer:|$)", llm_output, re.DOTALL
            )
            thought = thought_match.group(1).strip() if thought_match else llm_output.strip()

            # Parse Action: tool_name("query")
            action_match = re.search(r'Action:\s*(\w+)\("([^"]+)"\)', llm_output)

            step_data: Dict[str, Any] = {
                "step": step,
                "thought": thought,
                "action": None,
                "observation": None,
                "source": None,
            }

            if action_match:
                tool_name = action_match.group(1)
                tool_args = action_match.group(2)
                step_data["action"] = f'{tool_name}("{tool_args}")'
                step_data["source"] = tool_name

                observation = self._execute_tool(tool_name, tool_args)
                step_data["observation"] = observation

                conversation += f"{llm_output}\nObservation: {observation}\n"
                logger.log_event("TOOL_CALL", {
                    "step": step,
                    "tool": tool_name,
                    "args": tool_args,
                    "observation_length": len(observation),
                })
            else:
                # No valid action parsed — guide the LLM back on track
                observation = (
                    "No valid action found. Please use exactly this format: "
                    'tool_name("search query")'
                )
                step_data["observation"] = observation
                conversation += f"{llm_output}\nObservation: {observation}\n"
                logger.log_event("PARSE_ERROR", {
                    "step": step,
                    "raw_output": llm_output[:300],
                })

            trace.append(step_data)

        # Max steps reached without Final Answer
        logger.log_event("AGENT_END", {
            "steps": self.max_steps,
            "status": "max_steps_reached",
            "total_tokens": total_tokens,
        })
        return {
            "answer": (
                "Tôi không tìm được câu trả lời đầy đủ trong giới hạn bước. "
                "Bạn thử hỏi lại với câu hỏi cụ thể hơn nhé!"
            ),
            "trace": trace,
            "metrics": {
                "steps": self.max_steps,
                "total_tokens": total_tokens,
                "latency_ms": total_latency,
            },
        }

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """Gọi tool theo tên, trả về kết quả hoặc thông báo lỗi."""
        if tool_name not in self.tools:
            available = ", ".join(self.tools.keys())
            logger.log_event("TOOL_NOT_FOUND", {"tool": tool_name, "available": available})
            return f"Tool '{tool_name}' not found. Available tools: {available}"
        try:
            return self.tools[tool_name]["func"](args)
        except Exception as e:
            logger.log_event("TOOL_ERROR", {"tool": tool_name, "error": str(e)})
            return f"Tool '{tool_name}' encountered an error: {str(e)}"
