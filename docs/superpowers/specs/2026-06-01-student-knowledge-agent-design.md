# Design Spec: Student Knowledge Agent
**Date:** 2026-06-01  
**Lab:** Lab 3 — Chatbot vs ReAct Agent  
**Author:** HoThanhTien

---

## 1. Problem Statement

Sinh viên mất thời gian mỗi lần tìm thông tin vì tài liệu môn học nằm rải rác ở Discord, PDF, GitHub, LMS và Google Drive, dẫn đến việc hỏi lại TA hoặc sử dụng nhầm thông tin cũ.

**Solution:** AI Chatbot Agent tập trung — sinh viên hỏi 1 chỗ, agent tự tìm đúng nguồn và trả lời.

---

## 2. Architecture

### 2.1 Stack
- **Frontend:** HTML/CSS/JS thuần (index.html), serve qua nginx
- **Backend:** FastAPI + Uvicorn (Python)
- **Agent:** ReAct loop (Thought → Action → Observation)
- **Deploy:** Docker Compose (2 services: frontend:80, backend:8000)
- **LLM:** OpenAI GPT-4o (primary) / Gemini 1.5 Flash (fallback)
- **Data:** Mock knowledge base (Python dicts, giả lập 5 nguồn)

### 2.2 Component Flow
```
Browser (index.html)
  └─ POST /chat → FastAPI (main.py)
                    └─ ReActAgent.run(question)
                         ├─ discord_tool(query)   → Mock Discord data
                         ├─ pdf_tool(query)        → Mock PDF data
                         ├─ github_tool(query)     → Mock GitHub data
                         ├─ lms_tool(query)        → Mock LMS data
                         └─ drive_tool(query)      → Mock Drive data
```

### 2.3 Directory Structure
```
Lab3_HoThanhTien_1_6/
├── docker-compose.yml
├── frontend/
│   └── index.html              # Chat UI với trace viewer
└── backend/
    ├── Dockerfile
    ├── requirements.txt
    ├── .env                    # OPENAI_API_KEY, DEFAULT_PROVIDER
    ├── main.py                 # FastAPI: POST /chat, GET /health
    ├── chatbot.py              # Chatbot baseline (so sánh với agent)
    └── src/
        ├── agent/
        │   └── agent.py        # ReAct loop implementation
        ├── tools/
        │   ├── discord_tool.py
        │   ├── pdf_tool.py
        │   ├── github_tool.py
        │   ├── lms_tool.py
        │   └── drive_tool.py
        ├── core/
        │   ├── llm_provider.py
        │   ├── openai_provider.py
        │   └── gemini_provider.py
        └── telemetry/
            ├── logger.py
            └── metrics.py
```

---

## 3. Features & Scope

### 3.1 Câu hỏi được hỗ trợ
| Loại | Ví dụ | Nguồn |
|------|-------|-------|
| Deadline & Lịch nộp | "Lab 3 nộp khi nào?" | LMS, Discord |
| Tài liệu & Slide | "Slide buổi 3 ở đâu?" | Google Drive, LMS, PDF |
| Code & Repo | "Repo starter lab 3 ở đâu?" | GitHub |
| Thông báo mới nhất | "TA vừa thông báo gì?" | Discord |
| Điểm số & Rubric | "Cách tính điểm lab 3?" | LMS, PDF |

### 3.2 ReAct Loop
- **Max steps:** 5 (giống skeleton Lab 3)
- **Format:** `Thought:` → `Action: tool_name(args)` → `Observation:` → `Final Answer:`
- **Parser:** Regex extract action từ LLM output
- **Error handling:** Tool not found → log + retry với observation "Tool unavailable"

### 3.3 Chatbot Baseline
- `chatbot.py`: Gọi LLM trực tiếp, không có tools
- Dùng để so sánh với Agent trong report (Chatbot vs Agent)
- API endpoint: `POST /chat?mode=chatbot` vs `POST /chat?mode=agent`

---

## 4. Mock Data Design

Mỗi tool có knowledge base riêng (Python dict), keyword search đơn giản:

### discord_tool
```python
DISCORD_DATA = [
  {"channel": "#announcements", "date": "2026-05-31", "author": "TA_Minh",
   "content": "Lab 3 deadline extended to 01/06 23:59. Submit on LMS."},
  {"channel": "#general", "date": "2026-06-01", "author": "TA_Minh",
   "content": "Reminder: Use the starter repo on GitHub, branch main."},
]
```

### lms_tool
```python
LMS_DATA = [
  {"type": "assignment", "title": "Lab 3: ReAct Agent",
   "deadline": "2026-06-01 23:59", "points": 100,
   "submit_url": "https://lms.aivn.vn/lab3"},
  {"type": "rubric", "title": "Lab 3 Scoring",
   "content": "Group 60pts (base 45 + bonus 15) + Individual 40pts"},
]
```

### github_tool, pdf_tool, drive_tool — tương tự pattern trên.

---

## 5. API Design

### POST /chat
```json
Request:  { "message": "Lab 3 nộp khi nào?", "mode": "agent" }
Response: {
  "answer": "Lab 3 deadline là 01/06/2026 23:59...",
  "mode": "agent",
  "trace": [
    {"step": 1, "thought": "...", "action": "lms_tool(...)", "observation": "..."},
    {"step": 2, "thought": "...", "action": "discord_tool(...)", "observation": "..."}
  ],
  "metrics": { "steps": 2, "latency_ms": 1200, "total_tokens": 420 }
}
```

### GET /health
```json
{ "status": "ok", "provider": "openai", "model": "gpt-4o" }
```

---

## 6. Frontend (index.html)

- Chat bubble UI: user message bên phải, agent bên trái
- **Trace accordion:** Mỗi câu trả lời có nút "Xem trace" → expand Thought/Action/Observation từng step
- **Source badges:** Mỗi observation hiện badge nguồn (🎮 Discord / 📄 PDF / 🐙 GitHub / 🎓 LMS / 📁 Drive)
- **Mode toggle:** Switch giữa "Agent" và "Chatbot" để compare
- **Metrics bar:** Hiện latency + token count sau mỗi response

---

## 7. Docker Compose

```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: ./backend/.env
    volumes: ["./backend:/app"]

  frontend:
    image: nginx:alpine
    ports: ["80:80"]
    volumes: ["./frontend:/usr/share/nginx/html"]
```

Run: `docker compose up --build`

---

## 8. Telemetry & Logging

Kế thừa từ Lab 3 skeleton:
- `logger.py`: JSON log mỗi event (AGENT_START, TOOL_CALL, AGENT_END)
- `metrics.py`: Track latency_ms, token count, cost estimate per request
- Log file: `logs/YYYY-MM-DD.log`
- Dùng cho **Failure Analysis** trong group report

---

## 9. Lab 3 Scoring Map

| Rubric Item | Cách đạt |
|---|---|
| Chatbot Baseline (2pt) | `chatbot.py` + `/chat?mode=chatbot` |
| Agent v1 Working (7pt) | ReAct loop + 2+ tools hoạt động |
| Agent v2 Improved (7pt) | Fix failure từ v1, better prompt |
| Tool Design Evolution (4pt) | Doc tool spec v1→v2 trong report |
| Trace Quality (9pt) | JSON logs + trace trong frontend |
| Evaluation & Analysis (7pt) | So sánh chatbot vs agent metrics |
| Flowchart & Insight (5pt) | Diagram ReAct loop |
| Code Quality (4pt) | Clean, modular, telemetry |
| **Bonus: Live Demo (+5)** | Demo web UI cho instructor |
