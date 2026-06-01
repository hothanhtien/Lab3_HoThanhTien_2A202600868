# 🎓 Student Knowledge Agent — Lab 3

> **Agentic AI Bootcamp · Day 3** — Chatbot vs ReAct Agent  
> Tác giả: Hồ Thanh Tiên · 01/06/2026

AI Agent giúp sinh viên tìm thông tin môn học từ **1 chỗ duy nhất** thay vì phải tìm thủ công qua Discord, PDF, GitHub, LMS và Google Drive.

🌐 **Live Demo:** https://tien-ops.khoav4.com

---

## 📋 Mục lục

- [Tổng quan hệ thống](#tổng-quan)
- [Yêu cầu](#yêu-cầu)
- [Chạy local (Docker Compose)](#chạy-local)
- [Deploy lên server](#deploy-lên-server)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [API Reference](#api-reference)
- [Xem logs](#xem-logs)

---

## 🏗️ Tổng quan

```
Internet → Cloudflare Tunnel → nginx → FastAPI → ReActAgent → 5 Tools
                                  ↳ / (frontend HTML)
                                  ↳ /chat (backend API)
                                  ↳ /health (health check)
```

**Tech Stack:**
- **Backend:** Python 3.11, FastAPI, OpenAI GPT-4o-mini
- **Frontend:** HTML/CSS/JS thuần
- **Infra:** Docker Compose, nginx, Cloudflare Tunnel

---

## ✅ Yêu cầu

| Tool | Version |
|------|---------|
| Docker | ≥ 24.x |
| Docker Compose | ≥ 2.x |
| OpenAI API Key | — |

---

## 🚀 Chạy local

### 1. Clone repo

```bash
git clone https://github.com/<username>/Lab3_HoThanhTien_1_6.git
cd Lab3_HoThanhTien_1_6
```

### 2. Tạo file `.env`

```bash
cp backend/.env.example backend/.env
```

Mở `backend/.env` và điền API key:

```env
OPENAI_API_KEY=sk-proj-...
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o-mini
MAX_STEPS=5
```

### 3. Build và chạy

```bash
docker compose up --build
```

### 4. Mở browser

| Service | URL |
|---------|-----|
| 🌐 Chat UI | http://localhost |
| 🔌 API Health | http://localhost:8001/health |
| 📄 API Docs | http://localhost:8001/docs |

> **Lưu ý:** Nếu port 80 bị chiếm, nginx sẽ chạy internal only và cloudflared kết nối qua Docker network.

---

## 🖥️ Deploy lên server

### 1. Clone và cấu hình

```bash
git clone https://github.com/<username>/Lab3_HoThanhTien_1_6.git
cd Lab3_HoThanhTien_1_6

cp backend/.env.example backend/.env
# Điền OPENAI_API_KEY vào backend/.env
```

### 2. Cấu hình Cloudflare Tunnel

Copy credentials file vào folder `cloudflared/`:

```bash
cp /path/to/c6b31c18-84d2-4ba1-b763-0eea0709a225.json cloudflared/
```

File `cloudflared/config.yml` đã có sẵn:

```yaml
tunnel: c6b31c18-84d2-4ba1-b763-0eea0709a225
credentials-file: /etc/cloudflared/c6b31c18-84d2-4ba1-b763-0eea0709a225.json

ingress:
  - hostname: tien-ops.khoav4.com
    service: http://nginx:80
  - service: http_status:404
```

### 3. Chạy

```bash
docker compose up -d --build
```

### 4. Kiểm tra

```bash
# Tất cả services đang chạy?
docker compose ps

# Tunnel kết nối Cloudflare chưa?
docker compose logs cloudflared

# Backend OK?
curl https://tien-ops.khoav4.com/health
```

Expected response:
```json
{
  "status": "ok",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "tools": ["discord_tool", "pdf_tool", "github_tool", "lms_tool", "drive_tool"]
}
```

---

## 📁 Cấu trúc thư mục

```
Lab3_HoThanhTien_1_6/
├── docker-compose.yml          # Orchestrate backend + nginx + cloudflared
├── .gitignore
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env                    # ⚠️ KHÔNG commit — chứa API key
│   ├── .env.example            # Template để copy
│   ├── main.py                 # FastAPI: POST /chat, GET /health
│   ├── chatbot.py              # Chatbot baseline (không có tools)
│   └── src/
│       ├── agent/
│       │   └── agent.py        # ReAct loop: Thought→Action→Observation
│       ├── tools/
│       │   ├── discord_tool.py # Mock Discord data
│       │   ├── pdf_tool.py     # Mock PDF data
│       │   ├── github_tool.py  # Mock GitHub data
│       │   ├── lms_tool.py     # Mock LMS data
│       │   └── drive_tool.py   # Mock Google Drive data
│       ├── core/
│       │   ├── llm_provider.py     # Abstract base class
│       │   ├── openai_provider.py  # OpenAI implementation
│       │   └── gemini_provider.py  # Gemini implementation
│       └── telemetry/
│           ├── logger.py       # JSON structured logger
│           └── metrics.py      # Performance tracker
│
├── frontend/
│   └── index.html              # Chat UI
│
├── nginx/
│   └── nginx.conf              # Reverse proxy config
│
├── cloudflared/
│   ├── config.yml              # Tunnel config
│   └── *.json                  # ⚠️ Credentials — KHÔNG commit
│
└── slides/
    └── index.html              # Slide thuyết trình (12 slides)
```

---

## 📡 API Reference

### `POST /chat`

Gửi câu hỏi đến Agent hoặc Chatbot.

**Request:**
```json
{
  "message": "Lab 3 nộp khi nào?",
  "mode": "agent"
}
```

| Field | Type | Values | Default |
|-------|------|--------|---------|
| `message` | string | Câu hỏi bất kỳ | — |
| `mode` | string | `"agent"` hoặc `"chatbot"` | `"agent"` |

**Response:**
```json
{
  "answer": "Lab 3 deadline là 01/06/2026 23:59...",
  "mode": "agent",
  "trace": [
    {
      "step": 1,
      "thought": "Cần tìm deadline trên LMS",
      "action": "lms_tool(\"deadline lab 3\")",
      "observation": "[LMS Assignment] Lab 3: deadline 01/06 23:59",
      "source": "lms_tool"
    }
  ],
  "metrics": {
    "steps": 2,
    "total_tokens": 412,
    "latency_ms": 1840
  }
}
```

### `GET /health`

```json
{
  "status": "ok",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "tools": ["discord_tool", "pdf_tool", "github_tool", "lms_tool", "drive_tool"],
  "max_steps": 5
}
```

---

## 📊 Xem logs

```bash
# Realtime logs tất cả services
docker compose logs -f

# Chỉ backend
docker compose logs -f backend

# Xem agent trace logs (JSON)
docker compose exec backend cat logs/$(date +%Y-%m-%d).log

# Đọc đẹp với jq
docker compose exec backend cat logs/$(date +%Y-%m-%d).log | jq .

# Copy log ra ngoài
docker compose cp backend:/app/logs ./logs
```

**Log events:**

| Event | Ý nghĩa |
|-------|---------|
| `AGENT_START` | Bắt đầu xử lý câu hỏi |
| `TOOL_CALL` | Gọi tool + kết quả |
| `PARSE_ERROR` | LLM output sai format |
| `LLM_METRIC` | Latency, tokens, cost |
| `AGENT_END` | Kết thúc + status |

---

## 🛑 Dừng hệ thống

```bash
# Dừng
docker compose down

# Dừng và xóa volumes
docker compose down -v
```

---

## 📝 Lab 3 Scoring

| Rubric | Điểm | Trạng thái |
|--------|------|-----------|
| Chatbot Baseline | 2pt | ✅ `chatbot.py` |
| Agent v1 Working | 7pt | ✅ ReAct + 5 tools |
| Tool Design | 4pt | ✅ 5 tools có spec rõ |
| Trace Quality | 9pt | ✅ JSON logs + UI trace |
| Code Quality | 4pt | ✅ Modular, telemetry |
| **Live Demo Bonus** | **+5pt** | ✅ tien-ops.khoav4.com |
