# Deploying the Frontend + Edge Proxies to Vercel

This guide describes the lean deployment path that ships only the Vite frontend and a couple of Edge proxies. The heavy Python backend stays on your own infrastructure (Render, Railway, EC2, etc.) and Vercel simply forwards browser calls to it. The end result avoids the 250 MB serverless limit entirely while keeping the public demo fast.

---

## 1. Prerequisites

- Vercel CLI installed and authenticated (`npm install -g vercel && vercel login`).
- A reachable FastAPI backend URL (the value you will expose via `BACKEND_BASE`).
- Node 18+ locally for building the Vite app.

```bash
cd /path/to/NivHenn
vercel whoami
vercel link --confirm   # Select the niv-henn project when prompted
vercel env ls           # Sanity-check that env vars belong to this project
```

---

## 2. Repo layout relevant to Vercel

```
/                         (repo root)
├── .vercelignore         # strips Python + data blobs from deployments
├── api/
│   ├── search.ts         # Edge proxy → GET /search
│   └── analyze/listings.ts # Edge proxy → POST /analyze/listings
├── vercel.json           # Static build + Edge runtime declaration
└── NivHenn_OnlyUI/       # Vite frontend (built into `dist/`)
```

Everything else (Python packages, datasets, tests, etc.) is ignored during the deploy.

---

## 3. Environment variables

Set project-level environment variables in the Vercel dashboard (Project → Settings → Environment Variables) or via CLI:

| Name | Description | Typical value |
|------|-------------|----------------|
| `BACKEND_BASE` | Public HTTPS URL for the FastAPI service you host elsewhere | `https://your-backend.example.com` |
| `VITE_API_BASE` | Frontend fetch prefix. Already defaults to `/api` via `.env.production`, but configure in Vercel so previews match. | `/api` |

CLI example:

```bash
vercel env add BACKEND_BASE
vercel env add VITE_API_BASE
```

> **Note:** You no longer need `LIGHTWEIGHT_API`, `RAPIDAPI_KEY`, or any other Python-specific setting in Vercel because that workload is external.

---

## 4. Local smoke test

From the frontend folder run a production build so you know the UI compiles before shipping:

```bash
cd NivHenn_OnlyUI
npm install
npm run build
```

You should see the output in `NivHenn_OnlyUI/dist/`.

Optional: emulate the Vercel build locally.

```bash
cd ..
vercel build
```

---

## 5. Deploy

Back at the repo root:

```bash
vercel --prod --yes
```

The CLI uploads the pre-filtered repo (thanks to `.vercelignore`), runs the Vite static build, and wires the two Edge proxies. A production URL will be printed at the end.

---

## 6. Post-deploy checks

1. Visit `https://<project>.vercel.app/` → the UI should load instantly.
2. Open DevTools → Network → trigger a property search. Requests should hit `https://<project>.vercel.app/api/search?...` and respond with proxied data from `BACKEND_BASE`.
3. Select listings and run an analysis → network request posts to `/api/analyze/listings` and proxies through to your backend.

If anything fails, `vercel logs <deployment-url>` is your friend.

---

## 7. Troubleshooting

| Symptom | Likely fix |
|---------|------------|
| `500` with `BACKEND_BASE is not configured` | Double-check the environment variable in Vercel (Preview/Production). Redeploy after updating. |
| `404` from `/api/search` | Ensure the backend actually exposes `/search` and that the proxy path matches. |
| Browser fetching `http://localhost:8000` in production | The `.env.production` file forces `/api`, but if you created an override in Vercel remove it or set it to `/api`. |
| Build still tries to package Python | Confirm `.vercelignore` is in the root that Vercel builds from and that the project isn’t configured with a different "Root Directory". |
| Need additional endpoints | Copy the edge proxy pattern (tiny file, `runtime: "edge"`, `fetch` pointed at `BACKEND_BASE`). |

---

That’s it—deploys stay tiny, the public demo stays fast, and the heavy Python agents remain under your control.
