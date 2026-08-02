# React frontend — Release Finder

This folder contains the **React.js** version of the web UI. The PHP backend in `../app/` still handles all API calls and database access; React is only the user interface.

## Quick start (development)

You need **two terminals**:

**Terminal 1 — PHP API** (port 8080):

```bash
cd /path/to/spotify-playground
php -S 127.0.0.1:8080 -t public
```

**Terminal 2 — React dev server** (port 5173, proxies `/api` and `/static` to PHP):

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173/

## Production build

```bash
cd frontend
npm run build
```

This writes static files to `../public/app/`. Then start PHP as usual:

```bash
php -S 127.0.0.1:8080 -t public
```

Open http://127.0.0.1:8080/ — PHP serves the React app and the REST API.

## Folder structure

```
frontend/src/
├── main.jsx              # Entry point: mounts React into #root
├── App.jsx               # Route definitions (URL → page)
├── api/client.js         # fetch() wrappers for /api/* endpoints
├── context/
│   ├── I18nContext.jsx   # Translations (t(), locale)
│   └── AppContext.jsx    # Page title, banner, toast messages
├── pages/                # One component per screen
├── components/           # Reusable UI pieces
├── hooks/                # Custom React hooks (e.g. job polling)
└── utils/                # Pure helpers (paths, clipboard)
```

See the project README for database backup and full setup.
