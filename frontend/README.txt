# SideQuest deploy prep files

Copy files:

backend/config/settings.py -> firstPython/config/settings.py
backend/requirements.txt -> firstPython/requirements.txt
backend/build.sh -> firstPython/build.sh
backend/.env.example -> firstPython/.env.example
backend/runtime.txt -> firstPython/runtime.txt

frontend/src/api.js -> sidequest-frontend/src/api.js

Render backend:
- Build command: ./build.sh
- Start command: gunicorn config.wsgi:application

Vercel frontend:
- Environment variable: VITE_API_BASE_URL=https://YOUR-RENDER-BACKEND.onrender.com/api
