# Deploying to Vercel (Preview Demo)

This guide walks through the quickest path to ship the combined FastAPI backend and Vite frontend to Vercel so you can share a working demo link. The setup is intentionally lightweight—great for previews, not hardened production.

## 1. Prerequisites

- Vercel account with the [Vercel CLI](https://vercel.com/docs/cli) installed.
- Git repository pushed to a remote (GitHub or similar) or a local checkout ready to deploy via CLI.
- RapidAPI and OpenAI credentials (plus any other keys you rely on in `.env`).

```bash
npm install -g vercel
vercel login
```

## 2. Project layout recap

```
/                       # repo root
├── api/index.py        # Vercel serverless entrypoint importing FastAPI app
├── vercel.json         # Build + routing config for Vercel
├── src/                # FastAPI application code
└── NivHenn_OnlyUI/     # Vite + React frontend
```

The `vercel.json` file wires up two build targets:

1. `@vercel/static-build` → builds the Vite app (`npm run build`) and publishes the `dist` folder.
2. `@vercel/python` → exposes the FastAPI app through the `/api` serverless function.

## 3. Configure environment variables

Create the required environment variables on Vercel **before** deploying so both the frontend and backend can run:

| Name | Where it’s used | Example | Notes |
|------|-----------------|---------|-------|
| `RAPIDAPI_KEY` | FastAPI (serverless) | `sk_...` | Required for LoopNet requests |
| `OPENAI_API_KEY` | FastAPI (serverless) | `sk-...` | Required for agent analysis |
| `NEWS_API_KEY`, `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` | Optional extras | | Only if you already use them locally |
| `VITE_API_BASE` | Vite frontend | `/api` | Ensures the browser hits the co-located serverless API |

Using the CLI:

```bash
vercel env add RAPIDAPI_KEY
vercel env add OPENAI_API_KEY
vercel env add VITE_API_BASE
# repeat for any optional keys
```

You’ll be prompted for values and which environment (Development / Preview / Production) to bind them to. For demo purposes, setting Preview + Production is usually enough.

> **Tip:** To match your local dev experience, you can also run `vercel env pull .env.vercel` and then `source .env.vercel` before invoking the backend locally.

## 4. First deployment from the repo root

From `/Users/alonflorentin/Downloads/FreeLance/NivHenn` (or your clone path):

```bash
vercel --prod
```

Vercel will detect `vercel.json`, install dependencies for both projects, build the frontend, and package the FastAPI serverless function. The output will include a production URL (`https://<project>.vercel.app`).

For subsequent updates you can simply run:

```bash
vercel --prod
```

or use `vercel` (Preview) to test before promoting to Production.

## 5. Smoke test the deployment

After the deploy finishes:

1. Open `https://<project>.vercel.app/` – the UI should load.
2. Trigger a property search – network requests should target `https://<project>.vercel.app/api/search?...` (thanks to `VITE_API_BASE=/api`).
3. Check Vercel’s dashboard **Functions** tab for cold-start times or errors if anything fails.

## 6. Troubleshooting

| Symptom | Likely fix |
|---------|------------|
| `502` or `500` from `/api/search` | Confirm `RAPIDAPI_KEY` and other backend env variables are present in Vercel and valid. |
| Browser still calling `http://localhost:8000` | Ensure `VITE_API_BASE` is set to `/api` in Vercel **and** redeploy. Check that no `.env.production` file overrides it. |
| Large serverless payload / timeout | Increase memory or duration in `vercel.json` under `functions.api/index.py` (currently 2048 MB & 60 s). |
| Styling missing | Re-run `npm run build` locally to confirm Tailwind/postcss compile fine; if yes, redeploy. |

Once everything looks good, share the production URL—no additional configuration required for the recipients.

Happy demoing! 🚀
