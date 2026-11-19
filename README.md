# NammaPros Backend API

Production-grade Django REST API backend for NammaPros home services booking platform.

This backend is completely standalone and independent from any frontend or monorepo structure. It can be run and deployed on its own with standard Python and Docker tools.

---

## Quick Start (Local Development)

### 1. Prerequisites
- Python 3.12+
- (Optional) PostgreSQL and Redis (falls back to local SQLite if DATABASE_URL is not set)

### 2. Setup Virtual Environment
```bash
# In the backend directory
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Configure Environment Variables
```bash
cp .env.example .env
```
*(If `DATABASE_URL` is omitted, Django automatically uses local `db.sqlite3`)*

### 4. Run Migrations & Seed Catalog
```bash
python manage.py migrate
python manage.py seed_demo_catalog
```

### 5. Start Development Server
```bash
python manage.py runserver 127.0.0.1:8000
```
API is now running at [http://127.0.0.1:8000/api/v1/](http://127.0.0.1:8000/api/v1/).  
Health check endpoint: [http://127.0.0.1:8000/api/v1/health/](http://127.0.0.1:8000/api/v1/health/).

---

## Environment Variables

| Variable | Required | Description | Example / Default |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | Production | Django secret key | Generate secure random string |
| `DATABASE_URL` | Production | Postgres connection string (Neon / Cloud SQL) | `postgresql://user:pass@host/db?sslmode=require` |
| `REDIS_URL` | Production | Redis URL for caching & locks | `redis://localhost:6379/0` |
| `DJANGO_ALLOWED_HOSTS` | Production | Comma-separated list of allowed hostnames | `api.yourdomain.com,your-api.onrender.com` |
| `CORS_ALLOWED_ORIGINS` | Production | Comma-separated frontend origins | `https://www.yourdomain.com,https://your-frontend.vercel.app` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Production | Comma-separated origins for CSRF | `https://www.yourdomain.com,https://your-frontend.vercel.app` |
| `NAMMAPROS_ENV` | Optional | Environment mode (`development`, `staging`, `production`) | `production` |
| `DJANGO_DEBUG` | Optional | Debug mode | `"false"` in production |
| `FIREBASE_PROJECT_ID` | Optional | Firebase project for Phone Auth verification | `your-firebase-project` |
| `FIREBASE_WEB_API_KEY` | Optional | Firebase Web API key | Private key string |
| `CLOUDINARY_URL` | Optional | Cloudinary storage URL for media | `cloudinary://...` |
| `PORT` | Optional | Web server listening port | `8080` (or injected by PaaS) |

---

## Deployment Options

### 1. Render (Recommended PaaS)

1. Connect your repository to [Render](https://render.com).
2. Create a new **Web Service**.
3. If this code is in a `backend` subfolder, set **Root Directory** to `backend`. If in its own repository, leave Root Directory as `./`.
4. Environment: **Python** (or **Docker** using included `Dockerfile`).
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 60`
7. Pre-deploy Command: `python manage.py migrate --noinput`
8. Health Check Path: `/api/v1/health/`
9. In **Environment Variables**, configure `DATABASE_URL`, `REDIS_URL`, `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `DJANGO_SECRET_KEY`.
10. Click **Create Web Service**.

Alternatively, Render can use the included `render.yaml` blueprint.

---

### 2. Google Cloud Run

Deploy directly using the included standalone `Dockerfile`:

```bash
# In the backend directory:
gcloud run deploy nammapros-api \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars NAMMAPROS_ENV=production,DJANGO_DEBUG=false \
  --set-secrets DATABASE_URL=nammapros-db-url:latest,DJANGO_SECRET_KEY=django-secret-key:latest
```

---

### 3. Railway / Heroku

Because `backend/Procfile` and `backend/requirements.txt` are included at the root:
1. Connect the Git repository to Railway or Heroku.
2. If in a subfolder, configure the root directory to `backend`.
3. The platform automatically detects Python, installs dependencies from `requirements.txt`, and runs the `web` process defined in `Procfile`.
4. Add environment variables in the project settings.

---

### 4. Docker (Standalone Container / VPS)

```bash
# Build Docker image
docker build -t nammapros-backend .

# Run container
docker run -d \
  -p 8080:8080 \
  -e DJANGO_SECRET_KEY="your-secret-key" \
  -e DJANGO_DEBUG="false" \
  -e DJANGO_ALLOWED_HOSTS="*" \
  nammapros-backend
```

---

## Running Tests

```bash
pytest
```
Run targeted tests:
```bash
pytest tests/test_foundation.py
pytest tests/test_catalog_quick_view.py
```
