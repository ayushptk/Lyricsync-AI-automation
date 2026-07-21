# Debugging and Troubleshooting Guide

## 1. Hot-Reloading Issues (Next.js & Windows WSL2)
If you are modifying files in the `frontend/` folder on Windows and the changes are not reflecting in the browser, it is likely due to WSL2 file system event propagation issues.
- **Solution:** We have enabled `WATCHPACK_POLLING=true` in `docker-compose.yml` to force Webpack to poll for changes. If it is still not working, consider running `npm run dev` natively on your Windows host instead of inside Docker.

## 2. Line Ending Issues (CRLF vs LF)
Docker containers are Linux-based. If your files have Windows line endings (CRLF), bash scripts or configuration files inside the containers might fail with weird syntax errors (e.g., `\r: command not found`).
- **Solution:** Configure Git to checkout with LF line endings or configure your IDE (VS Code) to save files as LF (bottom right corner). Run `git config --global core.autocrlf false` if necessary.

## 3. Viewing Logs
To see what's happening inside the containers in real-time:
- **All Services:** `docker-compose logs -f`
- **FastAPI Backend:** `docker-compose logs -f api`
- **Celery Worker:** `docker-compose logs -f worker`
- **Next.js Frontend:** `docker-compose logs -f frontend`

## 4. Shell Access to Containers
If you need to manually run an FFmpeg command or check installed Python packages:
- `docker-compose exec api /bin/bash`
- `docker-compose exec worker /bin/bash`

## 5. Rebuilding After Dependency Changes
If you add new packages to `package.json` or `requirements.txt`, you must rebuild the containers:
- `docker-compose up -d --build`

## 6. Wiping the Database
If you need a fresh slate, you can tear down the volumes (this deletes all Postgres and Redis data!):
- `docker-compose down -v`
