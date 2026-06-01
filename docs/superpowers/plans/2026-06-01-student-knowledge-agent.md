# Student Knowledge Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a ReAct Agent chatbot giúp sinh viên tìm thông tin môn học từ 5 nguồn (Discord, PDF, GitHub, LMS, Drive) qua 1 giao diện chat duy nhất.

**Architecture:** FastAPI backend chứa ReAct loop agent với 5 mock-data tools; HTML/JS frontend chat UI với trace viewer; Docker Compose chạy backend (port 8000) + nginx frontend (port 80).

**Tech Stack:** Python 3.11, FastAPI, OpenAI GPT-4o, Docker Compose, nginx, HTML/CSS/JS thuần.

---

## File Map

| File | Trách nhiệm |
|------|-------------|
| `backend/.env` | API keys & config |
| `backend/requirements.txt` | Python dependencies |
| `backend/Dockerfile` | Backend container |
| `docker-compose.yml` | Orchestrate services |
| `backend/main.py` | FastAPI app, routes /chat & /health |
| `backend/chatbot.py` | Chatbot baseline (no tools) |
| `backend/src/agent/agent.py` | ReAct loop implementation |
| `backend/src/tools/discord_tool.py` | Mock Discord search |
| `backend/src/tools/pdf_tool.py` | Mock PDF search |
| `backend/src/tools/github_tool.py` | Mock GitHub search |
| `backend/src/tools/lms_tool.py` | Mock LMS search |
| `backend/src/tools/drive_tool.py` | Mock Drive search |
| `backend/src/core/llm_provider.py` | Abstract LLM interface |
| `backend/src/core/openai_provider.py` | OpenAI implementation |
| `backend/src/telemetry/logger.py` | JSON structured logger |
| `backend/src/telemetry/metrics.py` | Performance tracker |
| `frontend/index.html` | Chat UI với trace accordion |

---

## Task 1: Project scaffold + .env + Docker Compose

**Files:**
- Create: `backend/.env`
- Create: `backend/.env.example`
- Create: `backend/requirements.txt`
- Create: `backend/Dockerfile`
- Create: `docker-compose.yml`
- Create: `frontend/` (empty dir placeholder)
- Create: `.gitignore`

- [ ] **Step 1: Tạo cấu trúc thư mục**

```bash
mkdir -p backend/src/agent backend/src/tools backend/src/core backend/src/telemetry
mkdir -p frontend
touch backend/src/__init__.py backend/src/agent/__init__.py
touch backend/src/tools/__init__.py backend/src/core/__init__.py
touch backend/src/telemetry/__init__.py
```

- [ ] **Step 2: Tạo `backend/.env`**

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o
MAX_STEPS=5
```

- [ ] **Step 3: Tạo `backend/.env.example`**

```env
OPENAI_API_KEY=sk-...
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o
MAX_STEPS=5
```

- [ ] **Step 4: Tạo `backend/requirements.txt`**

```txt
fastapi==0.111.0
uvicorn[standard]==0.30.1
openai==1.35.0
python-dotenv==1.0.1
pydantic==2.7.4
```

- [ ] **Step 5: Tạo `backend/Dockerfile`**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

- [ ] **Step 6: Tạo `docker-compose.yml`**

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    volumes:
      - ./backend:/app
    restart: unless-stopped

  frontend:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./frontend:/usr/share/nginx/html:ro
    depends_on:
      - backend
    restart: unless-stopped
```

- [ ] **Step 7: Tạo `.gitignore`**

```gitignore
backend/.env
backend/__pycache__/
backend/src/**/__pycache__/
backend/logs/
*.pyc
.env
```

- [ ] **Step 8: Commit**

```bash
git add .
git commit -m "feat: project scaffold, .env, docker-compose"
```

---

## Task 2: Telemetry — Logger & Metrics

**Files:**
- Create: `backend/src/telemetry/logger.py`
- Create: `backend/src/telemetry/metrics.py`

- [ ] **Step 1: Tạo `backend/src/telemetry/logger.py`**

```python
import logging
import json
import os
from datetime import datetime
from typing import Any, Dict


class IndustryLogger:
    def __init__(self, name: str = "AI-Lab-Agent", log_dir: str = "logs"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        if self.logger.handlers:
            return
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
        file_handler = logging.FileHandler(log_file)
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log_event(self, event_type: str, data: Dict[str, Any]):
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "data": data,
        }
        self.logger.info(json.dumps(payload))

    def info(self, msg: str):
        self.logger.info(msg)

    def error(self, msg: str, exc_info: bool = True):
        self.logger.error(msg, exc_info=exc_info)


logger = IndustryLogger()
```

- [ ] **Step 2: Tạo `backend/src/telemetry/metrics.py`**

```python
from typing import Dict
from src.telemetry.logger import logger

# Pricing per 1K tokens (gpt-4o)
PRICING = {
    "gpt-4o":          {"prompt": 0.005, "completion": 0.015},
    "gpt-4o-mini":     {"prompt": 0.00015, "completion": 0.0006},
    "gemini-1.5-flash":{"prompt": 0.000075, "completion": 0.0003},
}


class PerformanceTracker:
    def __init__(self):
        self.session_metrics = []

    def track_request(self, provider: str, model: str, usage: Dict[str, int], latency_ms: int):
        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "latency_ms": latency_ms,
            "cost_usd": self._calculate_cost(model, usage),
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)
        return metric

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        pricing = PRICING.get(model, {"prompt": 0.01, "completion": 0.03})
        prompt_cost = (usage.get("prompt_tokens", 0) / 1000) * pricing["prompt"]
        completion_cost = (usage.get("completion_tokens", 0) / 1000) * pricing["completion"]
        return round(prompt_cost + completion_cost, 6)


tracker = PerformanceTracker()
```

- [ ] **Step 3: Commit**

```bash
git add backend/src/telemetry/
git commit -m "feat: telemetry logger and metrics tracker"
```

---

## Task 3: LLM Provider — Abstract + OpenAI

**Files:**
- Create: `backend/src/core/llm_provider.py`
- Create: `backend/src/core/openai_provider.py`

- [ ] **Step 1: Tạo `backend/src/core/llm_provider.py`**

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class LLMProvider(ABC):
    def __init__(self, model_name: str, api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns dict with keys:
          - content: str
          - usage: {prompt_tokens, completion_tokens, total_tokens}
          - latency_ms: int
          - provider: str
        """
        pass
```

- [ ] **Step 2: Tạo `backend/src/core/openai_provider.py`**

```python
import os
import time
from typing import Dict, Any, Optional
from openai import OpenAI
from src.core.llm_provider import LLMProvider
from src.telemetry.metrics import tracker


class OpenAIProvider(LLMProvider):
    def __init__(self, model_name: str = "gpt-4o", api_key: Optional[str] = None):
        super().__init__(model_name, api_key or os.getenv("OPENAI_API_KEY"))
        self.client = OpenAI(api_key=self.api_key)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start = time.time()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0,
        )
        latency_ms = int((time.time() - start) * 1000)
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
        tracker.track_request("openai", self.model_name, usage, latency_ms)
        return {
            "content": response.choices[0].message.content,
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": "openai",
        }
```

- [ ] **Step 3: Commit**

```bash
git add backend/src/core/
git commit -m "feat: LLM provider abstraction and OpenAI implementation"
```

---

## Task 4: Mock Knowledge Base — 5 Tools

**Files:**
- Create: `backend/src/tools/discord_tool.py`
- Create: `backend/src/tools/pdf_tool.py`
- Create: `backend/src/tools/github_tool.py`
- Create: `backend/src/tools/lms_tool.py`
- Create: `backend/src/tools/drive_tool.py`

> Pattern chung: mỗi tool có `MOCK_DATA` (list of dicts) và hàm `search(query: str) -> str` thực hiện keyword search đơn giản.

- [ ] **Step 1: Tạo `backend/src/tools/discord_tool.py`**

```python
from typing import List, Dict

MOCK_DATA: List[Dict] = [
    {
        "channel": "#announcements",
        "date": "2026-06-01",
        "author": "TA_Minh",
        "content": "Lab 3 deadline is TODAY 01/06/2026 at 23:59. Submit via LMS. No late submissions accepted.",
    },
    {
        "channel": "#announcements",
        "date": "2026-05-30",
        "author": "TA_Minh",
        "content": "Lab 3 has been released! Fork the starter repo at github.com/aivn-course/lab3 and start from branch 'main'.",
    },
    {
        "channel": "#general",
        "date": "2026-06-01",
        "author": "TA_Linh",
        "content": "Reminder: individual report must be placed in report/individual_reports/ folder before submitting.",
    },
    {
        "channel": "#q-and-a",
        "date": "2026-05-31",
        "author": "TA_Minh",
        "content": "For Lab 3, you need at least 2 tools to get Agent v1 points. More tools = bonus points.",
    },
    {
        "channel": "#general",
        "date": "2026-05-29",
        "author": "Instructor_Nam",
        "content": "Day 3 lecture slides have been uploaded to Google Drive. Check the #resources channel for the link.",
    },
]


def search(query: str) -> str:
    """Search Discord messages for relevant information."""
    query_lower = query.lower()
    results = [
        item for item in MOCK_DATA
        if any(word in item["content"].lower() for word in query_lower.split())
    ]
    if not results:
        return "No relevant Discord messages found."
    output = []
    for r in results[:3]:
        output.append(f"[Discord #{r['channel']} | {r['date']} | {r['author']}]\n{r['content']}")
    return "\n\n".join(output)


TOOL_SPEC = {
    "name": "discord_tool",
    "description": (
        "Search Discord announcements and Q&A messages from TAs and instructors. "
        "Use for: latest announcements, deadline reminders, TA tips, class updates."
    ),
    "func": search,
}
```

- [ ] **Step 2: Tạo `backend/src/tools/lms_tool.py`**

```python
from typing import List, Dict

MOCK_DATA: List[Dict] = [
    {
        "type": "assignment",
        "title": "Lab 3: Chatbot vs ReAct Agent",
        "deadline": "2026-06-01 23:59",
        "points": 100,
        "submit_url": "https://lms.aivn.vn/courses/1/assignments/lab3",
        "description": "Implement a ReAct agent with at least 2 tools. Submit code + group report + individual report.",
    },
    {
        "type": "assignment",
        "title": "Lab 2: FastAPI + OpenAI Integration",
        "deadline": "2026-05-29 23:59",
        "points": 100,
        "submit_url": "https://lms.aivn.vn/courses/1/assignments/lab2",
        "description": "Build a REST API with FastAPI that integrates OpenAI chat completion.",
    },
    {
        "type": "rubric",
        "title": "Lab 3 Scoring Rubric",
        "content": (
            "Group Score (max 60): Chatbot Baseline 2pt, Agent v1 7pt, Agent v2 7pt, "
            "Tool Design 4pt, Trace Quality 9pt, Evaluation 7pt, Flowchart 5pt, Code Quality 4pt. "
            "Bonus (max +15): Extra Monitoring +3, Extra Tools +2, Failure Handling +3, Live Demo +5, Ablation +2. "
            "Individual Score (max 40): Technical Contribution 15pt, Debugging Case Study 10pt, "
            "Personal Insights 10pt, Future Improvements 5pt."
        ),
    },
    {
        "type": "course_info",
        "title": "Course Schedule",
        "content": (
            "Day 1 (28/05): Python + OpenAI API basics. "
            "Day 2 (29/05): AI Product Design. "
            "Day 3 (01/06): ReAct Agents. "
            "Day 4 (02/06): Multi-Agent Systems. "
            "Final Project deadline: 05/06/2026."
        ),
    },
]


def search(query: str) -> str:
    """Search LMS for assignments, deadlines, rubrics, and course info."""
    query_lower = query.lower()
    results = [
        item for item in MOCK_DATA
        if any(word in str(item).lower() for word in query_lower.split())
    ]
    if not results:
        return "No relevant LMS content found."
    output = []
    for r in results[:3]:
        if r["type"] == "assignment":
            output.append(
                f"[LMS Assignment] {r['title']}\n"
                f"Deadline: {r['deadline']} | Points: {r['points']}\n"
                f"Submit: {r['submit_url']}\n{r['description']}"
            )
        else:
            output.append(f"[LMS {r['type'].title()}] {r['title']}\n{r['content']}")
    return "\n\n".join(output)


TOOL_SPEC = {
    "name": "lms_tool",
    "description": (
        "Search the Learning Management System (LMS) for assignments, deadlines, "
        "rubrics, scoring criteria, and course schedule. "
        "Use for: submission deadlines, point breakdown, assignment requirements."
    ),
    "func": search,
}
```

- [ ] **Step 3: Tạo `backend/src/tools/github_tool.py`**

```python
from typing import List, Dict

MOCK_DATA: List[Dict] = [
    {
        "repo": "aivn-course/lab3",
        "type": "repo",
        "url": "https://github.com/aivn-course/lab3",
        "description": "Lab 3 starter code: Chatbot vs ReAct Agent. Fork this repo to start.",
        "default_branch": "main",
        "submit_branch": "Fork the repo, work on main, submit your GitHub link on LMS.",
    },
    {
        "repo": "aivn-course/lab3",
        "type": "file",
        "path": "src/agent/agent.py",
        "description": "ReActAgent skeleton class. Implement the run() method and _execute_tool() method.",
    },
    {
        "repo": "aivn-course/lab3",
        "type": "file",
        "path": "requirements.txt",
        "description": "Dependencies: fastapi, uvicorn, openai, python-dotenv, pydantic.",
    },
    {
        "repo": "aivn-course/lab3",
        "type": "issue",
        "title": "How to run locally without Docker?",
        "answer": "cd backend && pip install -r requirements.txt && uvicorn main:app --reload",
    },
    {
        "repo": "aivn-course/lab2",
        "type": "repo",
        "url": "https://github.com/aivn-course/lab2",
        "description": "Lab 2 reference solution: FastAPI + OpenAI. You can reuse the provider pattern.",
    },
]


def search(query: str) -> str:
    """Search GitHub repos, files, and issues for course code."""
    query_lower = query.lower()
    results = [
        item for item in MOCK_DATA
        if any(word in str(item).lower() for word in query_lower.split())
    ]
    if not results:
        return "No relevant GitHub content found."
    output = []
    for r in results[:3]:
        if r["type"] == "repo":
            output.append(
                f"[GitHub Repo] {r['repo']}\nURL: {r['url']}\n{r['description']}\n"
                f"Branch: {r.get('default_branch', 'main')} | {r.get('submit_branch', '')}"
            )
        elif r["type"] == "file":
            output.append(f"[GitHub File] {r['repo']}/{r['path']}\n{r['description']}")
        else:
            output.append(f"[GitHub Issue] {r['title']}\nAnswer: {r['answer']}")
    return "\n\n".join(output)


TOOL_SPEC = {
    "name": "github_tool",
    "description": (
        "Search GitHub repositories, files, and issues for course code and starter templates. "
        "Use for: starter repo links, which branch to use, how to run code, file structure questions."
    ),
    "func": search,
}
```

- [ ] **Step 4: Tạo `backend/src/tools/pdf_tool.py`**

```python
from typing import List, Dict

MOCK_DATA: List[Dict] = [
    {
        "file": "Day3_ReAct_Agents_Lecture.pdf",
        "page": 5,
        "content": (
            "ReAct = Reasoning + Acting. The agent alternates between Thought (reasoning), "
            "Action (tool call), and Observation (tool result). This loop continues until "
            "the agent produces a Final Answer."
        ),
    },
    {
        "file": "Day3_ReAct_Agents_Lecture.pdf",
        "page": 12,
        "content": (
            "System Prompt Template for ReAct:\n"
            "You have access to: [list tools]. Use format:\n"
            "Thought: your reasoning\nAction: tool_name(argument)\n"
            "Observation: tool result\nFinal Answer: your answer"
        ),
    },
    {
        "file": "Lab3_Instructions.pdf",
        "page": 1,
        "content": (
            "Lab 3 Objectives: 1) Build chatbot baseline. 2) Implement ReAct loop with 2+ tools. "
            "3) Compare chatbot vs agent performance. 4) Document failure traces. "
            "5) Submit group report + individual report."
        ),
    },
    {
        "file": "Lab3_Instructions.pdf",
        "page": 3,
        "content": (
            "Grading: Group score max 60 (base 45 + bonus 15). Individual score max 40. "
            "Total = MIN(60, group_base + group_bonus) + individual. "
            "Fail Early Learn Fast: document your failures — it's worth points!"
        ),
    },
    {
        "file": "Course_Syllabus.pdf",
        "page": 2,
        "content": (
            "Course: Agentic AI Bootcamp (5 days). Tools used: Python, FastAPI, OpenAI API, "
            "Docker, LangGraph (Day 4-5). Evaluation: 5 labs (100pts each) + final project."
        ),
    },
]


def search(query: str) -> str:
    """Search PDF documents (lecture slides, lab instructions, syllabus)."""
    query_lower = query.lower()
    results = [
        item for item in MOCK_DATA
        if any(word in item["content"].lower() for word in query_lower.split())
    ]
    if not results:
        return "No relevant PDF content found."
    output = []
    for r in results[:3]:
        output.append(f"[PDF: {r['file']} | Page {r['page']}]\n{r['content']}")
    return "\n\n".join(output)


TOOL_SPEC = {
    "name": "pdf_tool",
    "description": (
        "Search PDF documents including lecture slides, lab instruction PDFs, and course syllabus. "
        "Use for: concept explanations, lab objectives, grading criteria from official documents."
    ),
    "func": search,
}
```

- [ ] **Step 5: Tạo `backend/src/tools/drive_tool.py`**

```python
from typing import List, Dict

MOCK_DATA: List[Dict] = [
    {
        "type": "folder",
        "name": "Day 3 — ReAct Agents",
        "url": "https://drive.google.com/drive/folders/day3",
        "contents": ["Day3_ReAct_Agents_Lecture.pdf", "Lab3_Instructions.pdf", "Lab3_Demo_Video.mp4"],
    },
    {
        "type": "file",
        "name": "Day3_ReAct_Agents_Lecture.pdf",
        "url": "https://drive.google.com/file/day3-lecture",
        "uploaded": "2026-06-01",
        "description": "Lecture slides for Day 3: ReAct pattern, tool design, tracing and evaluation.",
    },
    {
        "type": "file",
        "name": "Lab3_Demo_Video.mp4",
        "url": "https://drive.google.com/file/lab3-demo",
        "uploaded": "2026-06-01",
        "description": "Demo video showing a working ReAct agent answering multi-step questions.",
    },
    {
        "type": "file",
        "name": "Course_Syllabus.pdf",
        "url": "https://drive.google.com/file/syllabus",
        "uploaded": "2026-05-28",
        "description": "Full course syllabus: schedule, grading policy, tools required.",
    },
    {
        "type": "folder",
        "name": "All Labs — Starter Code",
        "url": "https://drive.google.com/drive/folders/labs",
        "contents": ["Lab1_starter.zip", "Lab2_starter.zip", "Lab3_starter.zip"],
    },
]


def search(query: str) -> str:
    """Search Google Drive for course files and folders."""
    query_lower = query.lower()
    results = [
        item for item in MOCK_DATA
        if any(word in str(item).lower() for word in query_lower.split())
    ]
    if not results:
        return "No relevant Google Drive files found."
    output = []
    for r in results[:3]:
        if r["type"] == "folder":
            output.append(
                f"[Drive Folder] {r['name']}\nURL: {r['url']}\nContents: {', '.join(r['contents'])}"
            )
        else:
            output.append(
                f"[Drive File] {r['name']}\nURL: {r['url']} | Uploaded: {r.get('uploaded', 'N/A')}\n"
                f"{r.get('description', '')}"
            )
    return "\n\n".join(output)


TOOL_SPEC = {
    "name": "drive_tool",
    "description": (
        "Search Google Drive for course files, lecture slides, demo videos, and starter code zips. "
        "Use for: finding where slides are stored, downloading lab materials, video demos."
    ),
    "func": search,
}
```

- [ ] **Step 6: Commit**

```bash
git add backend/src/tools/
git commit -m "feat: 5 mock knowledge base tools (discord, pdf, github, lms, drive)"
```

---

## Task 5: ReAct Agent Implementation

**Files:**
- Create: `backend/src/agent/agent.py`

- [ ] **Step 1: Tạo `backend/src/agent/agent.py`**

```python
import re
import os
from typing import List, Dict, Any
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger


class ReActAgent:
    """ReAct Agent: Thought → Action → Observation loop."""

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = {t["name"]: t for t in tools}
        self.max_steps = max_steps

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            [f"- {name}: {spec['description']}" for name, spec in self.tools.items()]
        )
        return f"""You are a helpful assistant for students. You have access to these tools:

{tool_descriptions}

Use EXACTLY this format for every response until you have a Final Answer:

Thought: <your reasoning about what to do next>
Action: <tool_name>("<search query")

When you have enough information, respond with:

Thought: I now have enough information to answer.
Final Answer: <your complete answer to the student>

Rules:
- Always start with Thought:
- Action format must be: tool_name("query") — use double quotes
- Only call ONE action per turn
- After getting an Observation, continue with the next Thought
- Do NOT make up information — only use what you got from tools
"""

    def run(self, user_input: str) -> Dict[str, Any]:
        """Run the ReAct loop. Returns answer + trace."""
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

            # Parse Final Answer
            if "Final Answer:" in llm_output:
                final_answer = llm_output.split("Final Answer:")[-1].strip()
                logger.log_event("AGENT_END", {
                    "steps": step, "total_tokens": total_tokens, "status": "success"
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

            # Parse Thought + Action
            thought_match = re.search(r"Thought:\s*(.+?)(?=Action:|Final Answer:|$)", llm_output, re.DOTALL)
            action_match = re.search(r'Action:\s*(\w+)\("([^"]+)"\)', llm_output)

            thought = thought_match.group(1).strip() if thought_match else llm_output.strip()
            step_data = {"step": step, "thought": thought, "action": None, "observation": None}

            if action_match:
                tool_name = action_match.group(1)
                tool_args = action_match.group(2)
                step_data["action"] = f'{tool_name}("{tool_args}")'

                observation = self._execute_tool(tool_name, tool_args)
                step_data["observation"] = observation
                step_data["source"] = tool_name

                conversation += f"{llm_output}\nObservation: {observation}\n"
                logger.log_event("TOOL_CALL", {
                    "step": step, "tool": tool_name, "args": tool_args,
                    "observation_length": len(observation)
                })
            else:
                # No action found — LLM might be confused
                observation = "No valid action found. Please use format: tool_name(\"query\")"
                step_data["observation"] = observation
                conversation += f"{llm_output}\nObservation: {observation}\n"
                logger.log_event("PARSE_ERROR", {"step": step, "raw_output": llm_output[:200]})

            trace.append(step_data)

        logger.log_event("AGENT_END", {"steps": self.max_steps, "status": "max_steps_reached"})
        return {
            "answer": "I was unable to find a complete answer within the step limit. Please try rephrasing your question.",
            "trace": trace,
            "metrics": {"steps": self.max_steps, "total_tokens": total_tokens, "latency_ms": total_latency},
        }

    def _execute_tool(self, tool_name: str, args: str) -> str:
        if tool_name not in self.tools:
            logger.log_event("TOOL_NOT_FOUND", {"tool": tool_name})
            return f"Tool '{tool_name}' not found. Available tools: {', '.join(self.tools.keys())}"
        try:
            return self.tools[tool_name]["func"](args)
        except Exception as e:
            logger.log_event("TOOL_ERROR", {"tool": tool_name, "error": str(e)})
            return f"Tool '{tool_name}' encountered an error: {str(e)}"
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/agent/agent.py
git commit -m "feat: ReAct agent with Thought-Action-Observation loop"
```

---

## Task 6: Chatbot Baseline

**Files:**
- Create: `backend/chatbot.py`

- [ ] **Step 1: Tạo `backend/chatbot.py`**

```python
from typing import Dict, Any
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger


CHATBOT_SYSTEM_PROMPT = """You are a helpful assistant for students in an AI bootcamp.
Answer questions about course deadlines, materials, lab instructions, and assignments.
Be concise and helpful. If you don't know something specific, say so honestly."""


class Chatbot:
    """Baseline chatbot: no tools, direct LLM call."""

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def run(self, user_input: str) -> Dict[str, Any]:
        logger.log_event("CHATBOT_START", {"input": user_input, "model": self.llm.model_name})
        result = self.llm.generate(user_input, system_prompt=CHATBOT_SYSTEM_PROMPT)
        logger.log_event("CHATBOT_END", {"latency_ms": result["latency_ms"]})
        return {
            "answer": result["content"],
            "trace": [],
            "metrics": {
                "steps": 1,
                "total_tokens": result["usage"].get("total_tokens", 0),
                "latency_ms": result["latency_ms"],
            },
        }
```

- [ ] **Step 2: Commit**

```bash
git add backend/chatbot.py
git commit -m "feat: chatbot baseline for comparison with ReAct agent"
```

---

## Task 7: FastAPI Backend

**Files:**
- Create: `backend/main.py`

- [ ] **Step 1: Tạo `backend/main.py`**

```python
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

app = FastAPI(title="Student Knowledge Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM provider
llm = OpenAIProvider(
    model_name=os.getenv("DEFAULT_MODEL", "gpt-4o"),
    api_key=os.getenv("OPENAI_API_KEY"),
)

# Initialize agent and chatbot
TOOLS = [DISCORD_TOOL, PDF_TOOL, GITHUB_TOOL, LMS_TOOL, DRIVE_TOOL]
agent = ReActAgent(llm=llm, tools=TOOLS, max_steps=int(os.getenv("MAX_STEPS", 5)))
chatbot = Chatbot(llm=llm)


class ChatRequest(BaseModel):
    message: str
    mode: str = "agent"  # "agent" or "chatbot"


@app.post("/chat")
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if request.mode == "chatbot":
        result = chatbot.run(request.message)
    else:
        result = agent.run(request.message)
    return {
        "answer": result["answer"],
        "mode": request.mode,
        "trace": result.get("trace", []),
        "metrics": result.get("metrics", {}),
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "provider": "openai",
        "model": os.getenv("DEFAULT_MODEL", "gpt-4o"),
        "tools": [t["name"] for t in TOOLS],
    }
```

- [ ] **Step 2: Test chạy local (không Docker)**

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Expected: Server starts, truy cập `http://localhost:8000/health` trả về:
```json
{"status": "ok", "provider": "openai", "model": "gpt-4o", "tools": [...]}
```

- [ ] **Step 3: Commit**

```bash
git add backend/main.py
git commit -m "feat: FastAPI backend with /chat and /health endpoints"
```

---

## Task 8: Frontend Chat UI

**Files:**
- Create: `frontend/index.html`

- [ ] **Step 1: Tạo `frontend/index.html`**

```html
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Student Knowledge Agent</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; height: 100vh; display: flex; flex-direction: column; }

    header { background: #1e293b; padding: 16px 24px; border-bottom: 1px solid #334155; display: flex; align-items: center; justify-content: space-between; }
    header h1 { font-size: 18px; font-weight: 600; color: #f1f5f9; }
    header h1 span { color: #6366f1; }

    .mode-toggle { display: flex; gap: 8px; }
    .mode-btn { padding: 6px 16px; border-radius: 20px; border: 1px solid #475569; background: transparent; color: #94a3b8; cursor: pointer; font-size: 13px; transition: all 0.2s; }
    .mode-btn.active { background: #6366f1; border-color: #6366f1; color: white; }

    #chat-container { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 16px; }

    .message { max-width: 75%; display: flex; flex-direction: column; gap: 6px; }
    .message.user { align-self: flex-end; align-items: flex-end; }
    .message.agent { align-self: flex-start; align-items: flex-start; }

    .bubble { padding: 12px 16px; border-radius: 12px; line-height: 1.6; font-size: 14px; }
    .user .bubble { background: #6366f1; color: white; border-bottom-right-radius: 4px; }
    .agent .bubble { background: #1e293b; border: 1px solid #334155; border-bottom-left-radius: 4px; }

    .metrics { font-size: 11px; color: #64748b; display: flex; gap: 12px; padding: 0 4px; }
    .metrics span { display: flex; align-items: center; gap: 4px; }

    .trace-toggle { font-size: 12px; color: #6366f1; cursor: pointer; padding: 4px; border: none; background: none; text-decoration: underline; }
    .trace-panel { background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 12px; font-size: 12px; display: none; max-width: 600px; }
    .trace-panel.open { display: block; }

    .trace-step { margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #1e293b; }
    .trace-step:last-child { border-bottom: none; margin-bottom: 0; }
    .trace-label { font-weight: 600; margin-bottom: 4px; }
    .trace-thought { color: #fbbf24; }
    .trace-action { color: #34d399; font-family: monospace; }
    .trace-observation { color: #60a5fa; white-space: pre-wrap; }

    .source-badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 500; margin-right: 4px; }
    .badge-discord_tool { background: #5865f2; color: white; }
    .badge-pdf_tool { background: #ef4444; color: white; }
    .badge-github_tool { background: #24292f; color: white; border: 1px solid #555; }
    .badge-lms_tool { background: #f59e0b; color: #1a1a1a; }
    .badge-drive_tool { background: #10b981; color: white; }

    .source-label { font-size: 11px; margin-bottom: 4px; color: #94a3b8; }

    .input-area { padding: 16px 24px; background: #1e293b; border-top: 1px solid #334155; display: flex; gap: 12px; }
    #message-input { flex: 1; background: #0f172a; border: 1px solid #334155; color: #e2e8f0; padding: 12px 16px; border-radius: 8px; font-size: 14px; outline: none; }
    #message-input:focus { border-color: #6366f1; }
    #send-btn { background: #6366f1; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 500; transition: background 0.2s; }
    #send-btn:hover { background: #5254cc; }
    #send-btn:disabled { background: #334155; cursor: not-allowed; }

    .typing { color: #64748b; font-size: 13px; padding: 8px 0; }
    .suggestions { display: flex; flex-wrap: wrap; gap: 8px; padding: 8px 24px 0; }
    .suggestion-chip { background: #1e293b; border: 1px solid #334155; color: #94a3b8; padding: 6px 14px; border-radius: 16px; font-size: 12px; cursor: pointer; transition: all 0.2s; }
    .suggestion-chip:hover { border-color: #6366f1; color: #6366f1; }
  </style>
</head>
<body>
  <header>
    <h1>🎓 Student <span>Knowledge Agent</span></h1>
    <div class="mode-toggle">
      <button class="mode-btn active" id="btn-agent" onclick="setMode('agent')">🤖 Agent</button>
      <button class="mode-btn" id="btn-chatbot" onclick="setMode('chatbot')">💬 Chatbot</button>
    </div>
  </header>

  <div class="suggestions">
    <span class="suggestion-chip" onclick="sendSuggestion(this)">Lab 3 nộp khi nào?</span>
    <span class="suggestion-chip" onclick="sendSuggestion(this)">Repo starter code lab 3 ở đâu?</span>
    <span class="suggestion-chip" onclick="sendSuggestion(this)">Slide buổi 3 ở đâu?</span>
    <span class="suggestion-chip" onclick="sendSuggestion(this)">Cách tính điểm lab 3 như thế nào?</span>
    <span class="suggestion-chip" onclick="sendSuggestion(this)">TA vừa thông báo gì mới nhất?</span>
  </div>

  <div id="chat-container"></div>

  <div class="input-area">
    <input id="message-input" type="text" placeholder="Hỏi về deadline, tài liệu, repo, điểm số..." onkeypress="if(event.key==='Enter') sendMessage()"/>
    <button id="send-btn" onclick="sendMessage()">Gửi ➤</button>
  </div>

  <script>
    const API_BASE = 'http://localhost:8000';
    let currentMode = 'agent';
    let traceCounter = 0;

    function setMode(mode) {
      currentMode = mode;
      document.getElementById('btn-agent').classList.toggle('active', mode === 'agent');
      document.getElementById('btn-chatbot').classList.toggle('active', mode === 'chatbot');
    }

    function sendSuggestion(el) {
      document.getElementById('message-input').value = el.textContent;
      sendMessage();
    }

    function sourceIcon(toolName) {
      const icons = { discord_tool: '🎮', pdf_tool: '📄', github_tool: '🐙', lms_tool: '🎓', drive_tool: '📁' };
      return icons[toolName] || '🔍';
    }

    function sourceName(toolName) {
      const names = { discord_tool: 'Discord', pdf_tool: 'PDF', github_tool: 'GitHub', lms_tool: 'LMS', drive_tool: 'Drive' };
      return names[toolName] || toolName;
    }

    function buildTraceHTML(trace) {
      if (!trace || trace.length === 0) return '';
      const id = 'trace-' + (++traceCounter);
      let steps = trace.map((s, i) => {
        const sourceBadge = s.source ? `<span class="source-badge badge-${s.source}">${sourceIcon(s.source)} ${sourceName(s.source)}</span>` : '';
        return `<div class="trace-step">
          <div class="trace-label">Step ${s.step}</div>
          <div class="trace-thought">💭 Thought: ${s.thought || ''}</div>
          ${s.action ? `<div class="trace-action">⚡ Action: ${s.action}</div>` : ''}
          ${s.observation ? `<div class="source-label">${sourceBadge}</div><div class="trace-observation">👁 Observation: ${s.observation}</div>` : ''}
        </div>`;
      }).join('');
      return `<button class="trace-toggle" onclick="document.getElementById('${id}').classList.toggle('open')">📋 Xem trace (${trace.length} bước)</button>
              <div id="${id}" class="trace-panel">${steps}</div>`;
    }

    async function sendMessage() {
      const input = document.getElementById('message-input');
      const msg = input.value.trim();
      if (!msg) return;
      input.value = '';

      const chat = document.getElementById('chat-container');
      chat.innerHTML += `<div class="message user"><div class="bubble">${msg}</div></div>`;
      chat.innerHTML += `<div class="message agent typing" id="typing">⏳ Agent đang tìm kiếm thông tin...</div>`;
      chat.scrollTop = chat.scrollHeight;
      document.getElementById('send-btn').disabled = true;

      try {
        const res = await fetch(`${API_BASE}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: msg, mode: currentMode })
        });
        const data = await res.json();

        document.getElementById('typing')?.remove();

        const sources = [...new Set((data.trace || []).filter(s => s.source).map(s => s.source))];
        const sourceBadges = sources.map(s => `<span class="source-badge badge-${s}">${sourceIcon(s)} ${sourceName(s)}</span>`).join('');

        const traceHTML = currentMode === 'agent' ? buildTraceHTML(data.trace) : '';
        const m = data.metrics || {};

        chat.innerHTML += `
          <div class="message agent">
            ${sourceBadges ? `<div class="source-label">${sourceBadges}</div>` : ''}
            <div class="bubble">${data.answer.replace(/\n/g, '<br>')}</div>
            <div class="metrics">
              <span>⏱ ${m.latency_ms || 0}ms</span>
              <span>🔤 ${m.total_tokens || 0} tokens</span>
              <span>🔄 ${m.steps || 1} bước</span>
            </div>
            ${traceHTML}
          </div>`;
      } catch (err) {
        document.getElementById('typing')?.remove();
        chat.innerHTML += `<div class="message agent"><div class="bubble" style="color:#ef4444">❌ Lỗi kết nối backend: ${err.message}</div></div>`;
      }
      document.getElementById('send-btn').disabled = false;
      chat.scrollTop = chat.scrollHeight;
    }
  </script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/index.html
git commit -m "feat: chat UI with trace accordion and source badges"
```

---

## Task 9: Build & Run với Docker Compose

- [ ] **Step 1: Build và chạy**

```bash
docker compose up --build
```

Expected output:
```
✔ backend  Built
✔ frontend Built
backend_1   | INFO: Application startup complete.
backend_1   | INFO: Uvicorn running on http://0.0.0.0:8000
```

- [ ] **Step 2: Kiểm tra health**

```bash
curl http://localhost:8000/health
```

Expected:
```json
{"status":"ok","provider":"openai","model":"gpt-4o","tools":["discord_tool","pdf_tool","github_tool","lms_tool","drive_tool"]}
```

- [ ] **Step 3: Mở browser**

Truy cập `http://localhost:80` — chat UI xuất hiện.

Gửi câu hỏi: `"Lab 3 nộp khi nào và repo ở đâu?"`

Expected: Agent chạy 2 bước, gọi `lms_tool` và `github_tool`, trả về deadline + link repo có trace.

- [ ] **Step 4: Test mode Chatbot vs Agent**

Click "💬 Chatbot", gửi câu hỏi `"Lab 3 repo ở đâu?"` — chatbot trả lời không có trace (hallucinate hoặc không biết).

Click "🤖 Agent" — agent gọi `github_tool`, tìm đúng repo URL.

- [ ] **Step 5: Final commit**

```bash
git add .
git commit -m "feat: full system running via docker compose"
```

---

## Task 10: Copy files sang Lab3_HoThanhTien_1_6 & submit

- [ ] **Step 1: Copy toàn bộ vào repo submit**

Tất cả code đã nằm trong `D:\AI_Vin\Lab3_HoThanhTien_1_6\` rồi — không cần copy thêm.

- [ ] **Step 2: Tạo individual report**

Tạo file `report/individual_reports/REPORT_HoThanhTien.md` dựa trên template, điền đủ 4 mục:
- I. Technical Contribution (list các file đã implement)
- II. Debugging Case Study (lấy 1 trace thất bại từ logs/)
- III. Personal Insights (chatbot vs agent)
- IV. Future Improvements

- [ ] **Step 3: Final commit**

```bash
git add report/
git commit -m "docs: add individual report"
```
