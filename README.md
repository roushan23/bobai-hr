# BOBAI HR

A white-label HRMS foundation built from [Horilla HR](https://github.com/horilla/horilla-hr), stable branch `2.0`. Employee management, recruitment, onboarding/offboarding, attendance, leave, payroll, performance, assets, helpdesk, projects, reports, APIs, and existing background jobs remain intact. This milestone changes basic branding and local development configuration only.

## Local development

Install Git and Docker Desktop with the Linux containers / WSL 2 backend. No host Python, PostgreSQL, Redis, or Node installation is needed. Start Docker Desktop before running these commands. The first source build downloads Horilla's dependencies and can take several minutes.

```powershell
git clone --branch bobai-foundation https://github.com/roushan23/bobai-hr.git
cd bobai-hr
Copy-Item .env.example .env
docker compose up --build -d --wait --wait-timeout 900
```

On macOS/Linux, replace `Copy-Item .env.example .env` with `cp .env.example .env`.

Open **http://localhost:8000/login/**. Use **Initialize Database** to enter the existing first-run wizard. The local setup password is the `DB_INIT_PASSWORD` value in `.env` (default: `bobai-local-setup`). Create your administrator, company, department and job position through that wizard, then sign in with the administrator credentials you chose. This password unlocks setup only; it is not an administrator login. Start with your own empty database; demo fixtures are optional and are not loaded by this setup.

If you are using this existing checkout at `D:\BOBcomp\BOBHR`, it already has `.env`; start with `docker compose up -d --wait --wait-timeout 900`.

The web app is bound to `127.0.0.1:8000`. PostgreSQL and Redis are available only inside the Docker network. To use another web port, change `WEB_PORT` in `.env` and recreate services with `docker compose up -d`; trusted CSRF origins follow the configured port. Environment values in `.env.example` are local development defaults. The upstream entrypoint replaces the default Django secret with a generated key persisted in the media volume.

## Daily commands

Run from the repository root:

```powershell
# Start / stop without deleting data
docker compose up -d --wait --wait-timeout 900
docker compose down

# Status / logs
docker compose ps
docker compose logs -f web scheduler

# Django commands
docker compose exec web python manage.py check
docker compose exec web python manage.py migrate --check
docker compose exec web python manage.py shell

# After adding migrations or changing static assets
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
docker compose restart web scheduler

# After changing dependencies or the Dockerfile
docker compose up --build -d --wait --wait-timeout 900

# Repeat the foundation smoke checks (rolls back its temporary HR records)
Get-Content scripts/verify_local.py -Raw | docker compose exec -T web python manage.py shell
```

On macOS/Linux, run the smoke check as `docker compose exec -T web python manage.py shell < scripts/verify_local.py`.

Source is bind-mounted into `/app`. Gunicorn reloads Python changes and Django reads templates afresh in development. Restart the scheduler after editing its Python code. Dependencies live inside the image; uploaded files and collected static files use named volumes.

Check the HTTP probes in PowerShell:

```powershell
Invoke-RestMethod http://localhost:8000/health/
Invoke-RestMethod http://localhost:8000/ready/
```

`/ready/` should report `database: ok`, `cache: ok`, and `scheduler: ok` after startup. The scheduler starts only after web has migrated the database and passed readiness. Keep exactly one scheduler because Horilla's payroll and backup jobs are not designed for multiple simultaneous runners. Readiness does not gate on scheduler registration, avoiding a circular startup dependency. `/health/` deliberately retains Horilla's API product identifier for compatibility with existing clients.

## Data and recovery

The Compose project is named `bobai-hr`. Its volumes preserve PostgreSQL (`postgres_data`), Redis (`redis_data`), uploads and generated secret (`media`), and collected assets (`staticfiles`) across container recreation and `docker compose down`.

To back up the local database without corrupting a binary dump through PowerShell redirection:

```powershell
docker compose exec db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/bobai-hr.dump'
docker compose cp db:/tmp/bobai-hr.dump ./bobai-hr.dump
```

Back up the media volume separately when you have real uploads. Do not change database credentials in `.env` after a database volume has been initialized unless you also update the database role; PostgreSQL's initialization variables only apply to an empty volume.

**Destructive local reset:** `docker compose down --volumes` permanently deletes this project's database, Redis data, uploads, and generated secret. Use only when intentionally discarding local data. Start again with `docker compose up --build -d --wait --wait-timeout 900`.

If startup fails, check `docker compose logs --tail 100 web scheduler db redis`. If port 8000 is occupied, set a different `WEB_PORT`. If Docker cannot connect to the engine, start Docker Desktop and confirm it is using Linux containers. Startup runs existing migrations, compiles missing translation catalogs, and collects static files; allow the first boot to finish before opening the app.

## Foundation verification

Verified locally on 7 October 2026: Docker image build and Compose startup, Django system checks, no unapplied migrations, PostgreSQL/Redis/scheduler readiness, logo and manifest HTTP serving, branded login and password-reset pages, CSRF protection, first-run setup authentication, administrator sign-in, and authenticated employee, attendance, recruitment, asset, payroll-contract, leave-type and admin pages. Browser inspection confirmed the supplied logo loads. The smoke check rolls back its temporary records; the local database remains ready for your own administrator setup. This is a foundation smoke check, not acceptance testing of every upstream HR workflow.

## Customization boundaries

- `bobai/settings.py` extends Horilla settings, enables the BOBAI app and requires PostgreSQL. Docker selects it through `DJANGO_SETTINGS_MODULE`.
- `bobai/context_processors.py` sets the default BOBAI name and logo while preserving Horilla's optional company branding.
- `bobai/static/bobai/images/logo.png` is the supplied **public/BobHR AI-Powered HRMS Logo (2).png**, copied unchanged. The product name in the UI is **BOBAI HR**.
- Existing templates have small hooks for `brand_name` and `brand_logo`; HR model names, migrations, URLs and core business logic retain their upstream identifiers.
- Future custom attendance, field attendance, payroll rules and AI administration should live in separate apps added through `bobai/settings.py`. No custom rules or AI features are implemented in this milestone.
- `docker-compose.yml` is the BOBAI local development stack. The inherited `docker-compose.prod.yml` is upstream reference material and is not validated with this stack. Production deployment requires separate configuration; do not combine the two files.

Django's admin branding also uses BOBAI HR. Horilla's original license, copyright notices and attribution remain. The unchanged upstream README is preserved at [docs/upstream/README.md](docs/upstream/README.md); its commands describe upstream Horilla, not this BOBAI configuration.

## Git lineage

Fork: https://github.com/roushan23/bobai-hr
Upstream: https://github.com/horilla/horilla-hr
Foundation branch: `bobai-foundation`
Starting upstream commit: `b947b0813936e7f1dcb16c63ff65326e45c9f709` (`2.0`)

The GitHub clone preserves upstream history. The supplied `horilla-hr-2.0.zip` was inspected as a reference; the stable Git checkout is the source of truth. The first BOBAI commit is made only after local runtime verification. `.env`, database dumps, uploads, translation binaries and runtime files are excluded from Git.

A fresh clone has only `origin`; add upstream once when needed:

```powershell
git remote add upstream https://github.com/horilla/horilla-hr.git
git fetch upstream 2.0
```

Review upstream changes on a separate branch before merging; preserve BOBAI customization boundaries and repeat smoke checks after upgrades. This repository retains the upstream [LGPL-2.1 license](LICENSE).
