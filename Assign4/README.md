# Assignment 4: Supabase Auth

A FastAPI implementation of Supabase email/password authentication.

## Setup

```powershell
cd Assign4
Copy-Item .env.example .env
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Set `SUPABASE_URL` and `SUPABASE_KEY` in `.env`. Use a publishable (or legacy anon) key only; never commit a service-role key.

## Endpoints

- `POST /auth/signup` - create an email/password account.
- `POST /auth/login` - return a Supabase access token.
- `GET /auth/me` - protected; use **Authorize** in `/docs` and paste the bearer token.
- `POST /auth/logout` - sign out the client session.
- `GET /health` and `GET /config` - service checks.

Hosted Supabase projects commonly require email confirmation. In that case signup succeeds without a session until the user confirms their email.