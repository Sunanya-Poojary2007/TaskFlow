# TaskFlow – Cloud-Based Task Management System with CI/CD

A Flask web application with automated testing, Docker, a GitHub Actions
CI/CD pipeline, and deployment to Render with a cloud PostgreSQL database.

**Stack:** Flask · SQLAlchemy · PostgreSQL (Neon/Supabase) · Bootstrap 5 · Chart.js ·
Pytest · flake8 · Docker · GitHub Actions · Render

## Features
- Register, log in, log out, profile and password change (hashed passwords, sessions)
- Tasks: create, edit, delete, priority, due date, status, search, filter
- Kanban board, task history, dashboard with Chart.js charts
- Dark/light mode, responsive layout, delete confirmation, loading buttons
- Security: password hashing, CSRF protection, ORM (no raw SQL), input validation,
  secure cookies, secrets only in environment variables
- 44 automated tests

---

## 1. Run locally (Windows PowerShell)

```powershell
cd task-manager
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python run.py
```
Open http://127.0.0.1:5000. Locally the app uses a SQLite file, so no database setup is needed.

If PowerShell blocks the activate script, run once:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## 2. Run the tests and the style check

```powershell
pytest -v
flake8 .
```

## 3. Run with Docker (optional, needs Docker Desktop)

```powershell
docker build -t taskflow .
docker run -p 8000:8000 -e SECRET_KEY=test taskflow
```
Open http://localhost:8000.

## 4. Create the cloud database (Neon, free)
1. Sign up at https://neon.tech and create a project.
2. Copy the **connection string** (it looks like
   `postgresql://user:password@host/dbname?sslmode=require`).
3. Keep it secret. You will paste it into Render in step 6.

Free-tier note: Neon may pause an idle database; the first request after a pause is slower.

## 5. Push the code to GitHub

```powershell
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/taskflow.git
git push -u origin main
```
Check that `.env` is **not** in the repository (it is listed in `.gitignore`).

## 6. Deploy on Render
1. Render dashboard → **New → Web Service** → connect your GitHub repo.
2. Runtime: **Docker**. Plan: **Free**.
3. **Auto-Deploy: Off** (GitHub Actions will trigger deploys instead).
4. Health check path: `/healthz`.
5. Environment variables:
   | Key | Value |
   |---|---|
   | `FLASK_ENV` | `production` |
   | `SECRET_KEY` | a long random text (`python -c "import secrets; print(secrets.token_hex(32))"`) |
   | `DATABASE_URL` | your Neon connection string |
6. Create the service. Open the URL it gives you and check that the app works.

Free-tier note: a free Render service sleeps after inactivity; the first request can take about 50 seconds.

## 7. Connect GitHub Actions to Render
1. Render → your service → **Settings → Deploy Hook** → copy the URL.
2. GitHub → your repo → **Settings → Secrets and variables → Actions → New repository secret**:
   - `RENDER_DEPLOY_HOOK_URL` = the deploy hook URL
   - `APP_URL` = your Render URL, for example `https://taskflow.onrender.com` (no trailing slash)
3. Make any small change, then:
   ```powershell
   git add .
   git commit -m "Test pipeline"
   git push
   ```
4. Open the **Actions** tab in GitHub and watch the pipeline.

## How the pipeline works (`.github/workflows/ci-cd.yml`)

| Job | What it does | If it fails |
|---|---|---|
| `test` | Checks out code, installs Python 3.12 and packages, runs `flake8`, then `pytest` | Nothing after it runs |
| `docker` | Builds the Docker image, starts it, calls `/healthz` | Deploy is blocked |
| `deploy` | Calls the Render deploy hook, then waits until the live `/healthz` answers | Workflow turns red |

- `deploy` runs only on a push to `main`, never on pull requests.
- `deploy` has `needs: [test, docker]`, so a failing test **blocks deployment**.
- To demonstrate this: break a test on purpose, push, and show the red ❌ and that Render did not deploy.

## Local vs cloud
| | Local | Cloud |
|---|---|---|
| Server | Flask dev server | gunicorn in a Docker container on Render |
| Database | SQLite file | PostgreSQL on Neon |
| Secrets | `.env` file | Render environment variables / GitHub secrets |

## Project structure
```
app/            Flask application (auth, tasks, main blueprints, templates, static)
tests/          Pytest tests
config.py       Settings read from environment variables
run.py          Entry point
Dockerfile      Container recipe
.github/workflows/ci-cd.yml   CI/CD pipeline
render.yaml     Optional Render blueprint
```

## Common problems
- **`ModuleNotFoundError`**: the virtual environment is not active or packages are not installed.
- **Pipeline fails at flake8**: read the line number in the log and fix the style issue.
- **Deploy step says secret not set**: add `RENDER_DEPLOY_HOOK_URL` in GitHub secrets.
- **Render shows a database error**: check `DATABASE_URL` and that it ends with `?sslmode=require`.
