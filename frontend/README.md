# Frontend (React + Vite)

Simple React UI for the Secure File Sharing Portal.

## Setup
```bash
npm install
cp .env.example .env
npm run dev
```

### Env
`VITE_API_BASE_URL=http://127.0.0.1:8010`
`VITE_GOOGLE_CLIENT_ID=...` (optional, for Google Sign-In)

## Pages
- `/login` — login form with link to register
- `/register` — registration
- `/dashboard` — send transfers, view sent/received, verify code, download files/zip

Token is stored in `localStorage` and sent via `Authorization: Bearer ...`.
