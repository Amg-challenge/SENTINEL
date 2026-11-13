# 🛡️ Sentinel

> When the bank sees something strange, it calls the right person: the one you trust.

Sentinel is a white-label module for banks. A person **chooses** to activate it and names a **trusted contact**. When an unusual operation happens - cash at the counter, a safe deposit box visit, a transfer to a new or foreign account - it is put **on hold** until the contact confirms or blocks it. Sentinel works **on top of** the bank's antifraud system (e.g. NetGuardians) and adds the missing link: verification by a person who really knows the client.

## Repository

```
sentinel/
├── backend/    Python: decision engine, simulation, FastAPI      → deployed on Railway
├── frontend/   React demo (generated with Lovable, then edited)  → deployed on Vercel
├── docs/       api.md (the contract between the two), project diary
└── pitch/      Project document v6 and work plan (single source of truth)
```

| Part | Read | Deploy |
|---|---|---|
| Back-end | [`backend/README.md`](backend/README.md) | Railway, root directory `backend` |
| Front-end | [`frontend/README.md`](frontend/README.md) | Vercel, root directory `frontend` |
| API contract | [`docs/api.md`](docs/api.md) | — |

## Deploy in two steps

**1 · Back-end on Railway**
New Project → Deploy from GitHub repo → `Amg-challenge/sentinel` → service **Settings → Root Directory: `backend`**. Railway installs `requirements.txt` and starts the API (`Procfile` / `railway.json`, health check on `/health`). Then **Settings → Networking → Generate Domain**. Optional variable: `ALLOWED_ORIGINS` = the Vercel URL (default: any origin).

**2 · Front-end on Vercel**
Add New → Project → import the same repo → **Root Directory: `frontend`** → Environment Variable `VITE_API_URL` = the Railway domain → Deploy.

Check: `https://<railway-domain>/health` answers `{"status": "ok"}` and `/docs` shows the API.

## How we work

1. Everyone works on their own branch (`modello`, `dati-economia`, `interfaccia`) and their own files; Pull Request to `main`.
2. Before a Pull Request, the tests pass: `cd backend && python -m pytest -q`.
3. The engine's signatures (`backend/README.md`) and the API (`docs/api.md`) change only with the group's agreement.
4. After any change to engine or scenarios: `python scripts/export_demo_data.py` (from `backend/`) to refresh the data and the front-end fallback.

## Calendar

| Date | Milestone |
|---|---|
| 29 November | First complete demo, end to end |
| 6 December | Code freeze |
| 10 December | Final deploy and backup video |
| 17 December | Presentation |
| Mid-January | Written deliverable (project diary, rebuttal of the jury's critique) |

---
*All data are synthetic: no real customer data.*
