# Frontend (React + Vite)

Simple React UI for the Secure File Sharing Portal.

## Setup
```bash
npm install
cp .env.example .env
npm run dev
```

### Env
`VITE_API_BASE_URL=http://localhost:8000`

## Pages
- `/login` — login form with link to register
- `/register` — registration
- `/owner` — upload, list, assign files
- `/client` — view and download own files

Token is stored in `localStorage` and sent via `Authorization: Bearer ...`.
