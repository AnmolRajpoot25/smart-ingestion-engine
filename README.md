# Smart Ingestion Engine

Django REST and React prototype for ingesting ESG activity data from SAP, utility electricity, and corporate travel sources.

## Live Services

### Frontend Service

- Live app: https://smart-ingestion-engine.vercel.app

### Backend Service

- Backend base URL: https://smart-ingestion-engine.onrender.com
- Upload endpoint: https://smart-ingestion-engine.onrender.com/api/ingest/upload/
- Records API: https://smart-ingestion-engine.onrender.com/api/review/records/
- Flagged records API: https://smart-ingestion-engine.onrender.com/api/review/records/flagged/
- Batches API: https://smart-ingestion-engine.onrender.com/api/review/batches/
- Parse errors API: https://smart-ingestion-engine.onrender.com/api/review/errors/

## Architecture

```mermaid
flowchart LR
    User["Analyst"]
    Frontend["React frontend<br/>Vercel"]
    Backend["Django REST API<br/>Render"]
    Parser["CSV parsers<br/>SAP, utility, travel"]
    Database[("PostgreSQL")]

    User --> Frontend
    Frontend -->|"upload + review API"| Backend
    Backend --> Parser
    Parser --> Backend
    Backend --> Database
```

## Main Capabilities

- Upload activity files for SAP, utility, or travel sources.
- Normalize source rows into one `EmissionRecord` model.
- Store parse failures as `ParseError` rows.
- Track each import with `IngestionBatch`.
- Record ingestion, approval, and rejection actions in `AuditEvent`.
- Use PostgreSQL in production and SQLite locally.

## Required Documentation

- `REQUIREMENTS.md`
- `ARCHITECTURE.md`
- `MODEL.md`
- `DECISIONS.md`
- `TRADEOFFS.md`
- `SOURCES.md`
- `DEPLOYMENT.md`

## Local Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Local Frontend

```bash
cd frontend
npm install
npm run dev
```

## Production Environment

Backend:

```env
DJANGO_SECRET_KEY=generate-a-long-random-secret
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=smart-ingestion-engine.onrender.com
DATABASE_URL=postgresql://user:password@host:5432/database
CORS_ALLOWED_ORIGINS=https://smart-ingestion-engine.vercel.app
CSRF_TRUSTED_ORIGINS=https://smart-ingestion-engine.onrender.com,https://smart-ingestion-engine.vercel.app
```

Frontend:

```env
VITE_API_BASE_URL=https://smart-ingestion-engine.onrender.com/api
```
