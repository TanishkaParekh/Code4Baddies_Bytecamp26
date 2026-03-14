# CascadeRx — Fullstack

Multi-drug cascade interaction checker. Detects hidden CYP450 enzyme bottlenecks that pairwise checkers miss.

## Project Structure

```
cascaderx-fullstack/
├── backend/          → Flask API (deploy to Railway)
└── frontend/         → Next.js 14 app (deploy to Vercel)
```

## Quick Start (local dev)

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                               # add your FEATHERLESS_API_KEY
python main.py
# → running on http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local                  # already points to localhost:8000
npm run dev
# → running on http://localhost:3000
```

---

## Deploy

### 1. Backend → Railway

1. Push the `backend/` folder to GitHub (can be a subdirectory)
2. Railway → New Project → Deploy from GitHub → select `backend/`
3. Railway auto-detects `Procfile` and runs gunicorn
4. Add env var in Railway dashboard:
   - `FEATHERLESS_API_KEY` = your key (or leave empty for mock LLM)
5. Note your Railway URL: `https://your-app.railway.app`

### 2. Frontend → Vercel

1. Push the `frontend/` folder to GitHub
2. Vercel → New Project → import → Framework: **Next.js**
3. Add env var in Vercel dashboard:
   - `NEXT_PUBLIC_API_URL` = `https://your-app.railway.app`
4. Deploy

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/analyze/stream` | Two-phase SSE: structured result + AI report |
| `POST` | `/analyze` | Structured JSON only (no LLM) |
| `GET`  | `/drugs/search?q=` | Autocomplete drug names |
| `GET`  | `/drugs/all` | Full CYP drug list |
| `GET`  | `/health` | Status check |

## Auth

Firebase Auth (Email/Password). Project: `code4baddies`.  
Login → Dashboard → Start Check → Checker page.
