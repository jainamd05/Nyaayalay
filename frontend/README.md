# Nyayalay Frontend

React + TypeScript + Vite frontend.

## Run

```bash
npm install
npm run dev
```

In development the app calls the API at `http://127.0.0.1:8000`.
To use a different backend, copy `.env.example` to `.env.local` and set
`VITE_API_BASE_URL`.

## Deploy (Vercel)

Set `VITE_API_BASE_URL` to the backend URL (e.g. `https://your-api.onrender.com`)
in the Vercel project settings and redeploy — Vite embeds it at build time.
