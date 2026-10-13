# Insurance Underwriting AI Assistant

**Human-in-the-loop underwriting workspace** — score policy applications, explain risk drivers, surface next-step suggestions, and keep final authority with the underwriter.

[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?style=flat-square)](#)
[![React](https://img.shields.io/badge/UI-React_18-61DAFB?style=flat-square)](#)
[![Gemini](https://img.shields.io/badge/AI-Gemini_optional-8E75B2?style=flat-square)](#)
[![Docker](https://img.shields.io/badge/Deploy-Docker_/_Render-2E8B57?style=flat-square)](#)

---

## Why this project

Mirrors real intake → risk review → decision workflows:

| Step | What happens |
| --- | --- |
| Intake | Auto / home / life / commercial applications |
| Score | Deterministic rules engine (works offline) |
| Explain | Optional **Google Gemini** narrative (token-light) |
| Guide | Actionable **next-step suggestions** for staff |
| Decide | Underwriter approves / refers / declines with notes |

> AI is **advisory only**. Licensed humans own the decision.

---

## Features

- JWT underwriter login + protected API
- Queue dashboard with portfolio stats & status filters
- Risk score, recommendation, premium indication, **suggestion checklist**
- Risk meter UI on application detail
- Seeded demo book of business
- Single Docker image (API + built React UI)
- Works **without** any LLM key

## Tech stack

| Layer | Choice |
| --- | --- |
| API | FastAPI, Pydantic, SQLAlchemy |
| Auth | OAuth2 password flow + JWT |
| DB | SQLite default (Postgres via `DATABASE_URL`) |
| UI | React 18, React Router, Vite |
| AI | Rules engine + optional Gemini (`gemini-2.0-flash`) |
| Deploy | Docker · Render Blueprint (`render.yaml`) |

---

## Quick start (local)

**Prereqs:** Python 3.11+, Node 18+

### Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
copy ..\.env.example ..\.env   # or: cp ../.env.example ../.env
uvicorn app.main:app --reload --app-dir . --port 8000
```

- API docs: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/api/health  

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: http://127.0.0.1:5173

### Demo login

```
Email:    underwriter@demo.com
Password: Demo@1234
```

---

## Optional Gemini explanations

Get a key from [Google AI Studio](https://aistudio.google.com/apikey), then set in `.env`:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
```

- Compact prompts + `maxOutputTokens=180` keep usage low  
- If the key is missing or the call fails, **rules still return** full scores, rationales, and suggestions  

---

## Docker

```bash
docker build -t underwriting-ai .
docker run --rm -p 8000:8000 -e GEMINI_API_KEY=your_key underwriting-ai
```

Open http://127.0.0.1:8000

---

## Deploy on Render

1. Push this repo to GitHub  
2. Render → **New** → **Blueprint** (or Web Service + Docker)  
3. Health check: `/api/health`  
4. Env vars:

| Key | Value |
| --- | --- |
| `SECRET_KEY` | generate |
| `DATABASE_URL` | `sqlite:///./underwriting.db` |
| `CORS_ORIGINS` | `*` |
| `DEMO_USER_EMAIL` | `underwriter@demo.com` |
| `DEMO_USER_PASSWORD` | `Demo@1234` |
| `GEMINI_API_KEY` | your key (optional) |
| `GEMINI_MODEL` | `gemini-2.0-flash` |

Container listens on `$PORT` (Render) or `8000` locally.

**Free tier:** cold starts; SQLite may reset on redeploy (fine for demos).

---

## API surface

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/auth/login` | OAuth2 form → JWT |
| GET | `/api/auth/me` | Current user |
| GET | `/api/applications` | List / filter queue |
| GET | `/api/applications/stats` | Dashboard metrics |
| POST | `/api/applications` | Create + score |
| GET | `/api/applications/{id}` | Detail (+ suggestions) |
| POST | `/api/applications/{id}/rescore` | Re-run engine |
| PATCH | `/api/applications/{id}/decision` | Record UW decision |
| GET | `/api/health` | Liveness (+ `gemini_configured`) |

---

## Project structure

```
backend/app/     FastAPI, auth, models, routers, scoring service
frontend/src/    React workspace (login, queue, detail, intake)
Dockerfile       Multi-stage production image
render.yaml      Render Blueprint
.env.example     Config template
```

## Design principles

1. **Assist, don’t replace** — AI advises; humans decide  
2. **Explainability** — scores ship with drivers + next steps  
3. **Auditability** — decisions and notes are stored  
4. **Portability** — SQLite + Docker demos; Postgres-ready  

## License

MIT — portfolio / demonstration use.
