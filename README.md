# Insurance Underwriting AI Assistant

Decision-support workspace for insurance staff reviewing policy applications. The system scores risk, recommends **approve / refer / decline**, explains the drivers, and suggests an indicative premium — while keeping **final authority with the underwriter**.

> Built to mirror real policy-management and underwriting workflows (intake → risk review → human decision), with a FastAPI backend, React UI, JWT auth, and an explainable scoring engine.

## Features

- JWT-authenticated underwriter workspace
- Application intake across **auto / home / life / commercial**
- Hybrid AI underwriting engine (deterministic rules + optional OpenAI narrative)
- Risk score, recommendation, explanation, and premium indication
- Queue dashboard with status filters and portfolio stats
- Human decision capture (approve / refer / decline) with notes
- Seeded demo book of business for instant walkthroughs
- Works fully offline without an LLM key

## Tech stack

| Layer | Choice |
| --- | --- |
| API | FastAPI, Pydantic, SQLAlchemy |
| Auth | OAuth2 password flow + JWT (python-jose, passlib/bcrypt) |
| DB | SQLite by default (swap `DATABASE_URL` for Postgres) |
| UI | React 18, React Router, Vite |
| AI | Rule-based risk engine; optional OpenAI explanation layer |
| Deploy | Docker single-service image (API + built UI) |

## Quick start (local)

### Prerequisites

- Python 3.11+
- Node.js 18+

### 1) Backend

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

API docs: http://127.0.0.1:8000/docs  
Health: http://127.0.0.1:8000/api/health

### 2) Frontend

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

## Docker (API + UI)

```bash
docker build -t underwriting-ai .
docker run --rm -p 8000:8000 underwriting-ai
```

Open http://127.0.0.1:8000

## Optional LLM explanations

Set in `.env`:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

If unset, the deterministic engine still returns full recommendations and rationales.

## API surface

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/auth/login` | OAuth2 form login → JWT |
| GET | `/api/auth/me` | Current user |
| GET | `/api/applications` | List / filter queue |
| GET | `/api/applications/stats` | Dashboard metrics |
| POST | `/api/applications` | Create + AI score |
| GET | `/api/applications/{id}` | Detail |
| POST | `/api/applications/{id}/rescore` | Re-run engine |
| PATCH | `/api/applications/{id}/decision` | Record UW decision |

## Project structure

```
backend/app/           FastAPI app, auth, models, routers, scoring service
frontend/src/          React workspace (login, queue, detail, intake)
Dockerfile             Production image build
.env.example           Configuration template
```

## Design principles

1. **Assist, don’t replace** — AI is advisory; humans own the decision.
2. **Explainability** — every score ships with readable drivers.
3. **Auditability** — decisions and notes are persisted with the application.
4. **Portability** — SQLite + Docker for demos; Postgres-ready via env.

## License

MIT — portfolio / demonstration use.
