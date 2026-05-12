# Agent Notes

## Project Shape
- `ujn/` is the Django 5.2 backend; run all `manage.py` commands from this directory.
- `frontend/` is the Vue 3 + TypeScript + Pinia + Vite app; `src/main.ts` wires Pinia/router, and routes live in `src/router/index.ts`.
- Backend APIs are function-based JSON views in `ujn/scoring/views.py`; there is no DRF layer despite some generic Django docs mentioning DRF.
- `ujn/scoring/sse.py` duplicates scoring/statistics helpers from `views.py` to avoid circular imports; update both paths when changing score/vote calculation semantics.

## Commands
- Backend setup/run: `cd ujn`, `pip install -r requirements.txt`, `python manage.py migrate`, `python manage.py runserver`.
- Backend tests: `cd ujn`, `python manage.py test scoring`; focused test example: `python manage.py test scoring.tests.JudgeSubmissionStateTests.test_submit_scores_can_be_read_back_from_another_client`.
- Model changes: `cd ujn`, `python manage.py makemigrations scoring`, then `python manage.py migrate`.
- Local seed data: `cd ujn`, `python manage.py init_test_data` creates sample categories, participants, and judges.
- Frontend setup/run: `cd frontend`, use `npm ci` when installing from the lockfile, then `npm run dev`.
- Frontend checks: `npm run type-check`; `npm run build-only` is just Vite bundling; `npm run build` runs type-check and build in parallel via `run-p`.

## Runtime Quirks
- `frontend/src/config/api.ts` intentionally keeps `API_BASE_URL` empty in dev and prod; dev traffic relies on Vite proxies for `/api` and `/media`, prod expects same-origin reverse proxying.
- In `frontend/vite.config.ts`, the SSE proxy for `/api/admin/scores/stream/` must stay before the generic `/api` proxy.
- `ujn/manage.py` loads `.env`; do not commit real `.env` files. Use `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CLEAR_PASSWORD`.
- `settings.py` uses SQLite at `ujn/db.sqlite3` by default; set `USE_MYSQL=1` plus `MYSQL_*` env vars to use an external MySQL-compatible database.
- `SiteConfig.admin_password` is intentionally plaintext because the frontend admin panel displays/edits it; do not silently replace it with Django password hashing without updating that flow.

## API And Data Flow
- Project URLs include `scoring.urls` under `/api/`; public config/categories/participants endpoints, judge token endpoints, and password-protected admin endpoints are all in that file.
- Judge access is by UUID token; admin API access is by the app-level password, not Django sessions.
- Many POST endpoints are `@csrf_exempt` by design for the decoupled frontend; replacing this needs a full auth/CSRF plan.
- After any score/vote mutation that should refresh the admin dashboard, call `score_event_bus.notify()` so `/api/admin/scores/stream/` clients update.
- `Score` is unique per `(judge, participant)` and `Vote` per `(judge, category, participant)`; submitted judge state is rebuilt from persisted rows, not from frontend local storage.

## Release/CI
- `.github/workflows/build-and-release.yml` runs on pushes to `main` and manual dispatch; it auto-increments a numeric tag, builds only the frontend with Node 20, then packages `frontend/dist` plus `ujn/`.
- `.github/workflows/dockerhub.yml` builds the root `Dockerfile` and pushes to DockerHub; it expects `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets, with optional `DOCKERHUB_IMAGE` repo variable.
- CI does not run Django tests, so run `python manage.py test scoring` locally for backend changes.
