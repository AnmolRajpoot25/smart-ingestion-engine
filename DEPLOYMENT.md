# Deployment

This project has a Django REST backend and a Vite/React frontend.

## Backend

Use these environment variables on the backend host:

```env
DJANGO_SECRET_KEY=generate-a-long-random-secret
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-backend-domain.com
DATABASE_URL=postgresql://user:password@host:5432/database
DATABASE_SSL_REQUIRE=True
DATABASE_CONN_MAX_AGE=60
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
CSRF_TRUSTED_ORIGINS=https://your-backend-domain.com,https://your-frontend-domain.com
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SECURE_HSTS_SECONDS=0
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=False
DJANGO_SECURE_HSTS_PRELOAD=False
```

Install and build commands:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Start command:

```bash
gunicorn config.wsgi:application
```

## Frontend

Use this environment variable on the frontend host:

```env
VITE_API_BASE_URL=https://your-backend-domain.com/api
```

Build command:

```bash
npm install
npm run build
```

Publish directory:

```txt
frontend/dist
```

## Notes

For Render, create a PostgreSQL database first and copy its `DATABASE_URL` into the backend service environment variables. Use the internal database URL when Render provides one for the same region.

Use persistent/cloud storage for uploaded media before relying on this in production.
