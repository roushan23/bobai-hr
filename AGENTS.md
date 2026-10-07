# BOBAI HR repository instructions

- Use the installed Superpowers plugin skills for work in this repository, especially verification before completion and code review when applicable. Read the relevant skills; follow the user's current scope and authorization.
- Preserve Horilla's core HR business logic, API compatibility, Python app names and migration lineage. Put future BOBAI behavior in separate apps and enable them through `bobai/settings.py`.
- Keep inherited settings lists shared: Horilla registers apps and context processors on `horilla.settings` during Django initialization.
- This milestone is local development only. Use PostgreSQL and the Docker Compose stack documented in `README.md`; keep exactly one scheduler.
- Verify relevant changes with `docker compose exec web python manage.py check`, `docker compose exec web python manage.py migrate --check`, and the foundation smoke command in `README.md` before claiming the stack works or committing runtime changes.
- Never commit `.env`, generated secrets, uploaded HR data, database backups, or temporary verification artifacts. Preserve upstream license and attribution.
