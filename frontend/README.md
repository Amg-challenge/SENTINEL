# Sentinel · front-end (pitch demo)

React app, deployed on **Vercel** (root directory: `frontend`). It calls the back-end API on Railway; the contract is [`../docs/api.md`](../docs/api.md).

## Status

Waiting for the export from **Lovable**. Until then this folder only holds `public/demo-fallback.json`.

## How the Lovable export lands here

1. Build the demo in Lovable from the prompt in `../docs/lovable-prompt.md` (written once the design direction is chosen: design, screens, scenarios, API).
2. When it looks right, export the code (GitHub sync or download) and copy **the contents** of the project into this folder, keeping `public/demo-fallback.json`.
3. From then on, the code is edited here, not in Lovable (two versions would drift apart).
4. Clean-up after the export: remove what the demo does not need (e.g. Supabase), check `npm run build`.

## Rules the front-end must follow

- API base URL from `import.meta.env.VITE_API_URL` (set in Vercel → Environment Variables).
- If the API does not answer within ~3 seconds, use `public/demo-fallback.json` (same shapes as `GET /demo-bundle`): the demo must never stop on stage.
- Demo state (consent, approve/block, simulated 30-minute and 72-hour clocks) lives in the front-end; the API is stateless.
- The money protected is a benefit for the client and the family: never present it as the reason the bank pays (document v6).

## Local run (after the export)

```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```
