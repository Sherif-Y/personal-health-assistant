# Personal Health Assistant

A personal-use application that connects to your own MyChart account (Epic on FHIR),
pulls your lab results and diagnostic reports, stores them locally, and uses Claude
to summarize them and answer questions — grounded in your real data, never guessed.

This is a single-user, local-first app: your data lives in a database on your own
machine, not a cloud service, and the app never sees or stores your MyChart password.

## What it does

- **Lab Results** — your labs grouped by the actual clinical panel (e.g. "Comprehensive
  Metabolic Panel," "CBC With Auto Differential"), one row per test showing the latest
  value, whether it's out of reference range, and the trend vs. your prior draw.
- **Trends** — a chart of any test's full history over time, with the reference range
  overlaid, grouped and searchable by panel.
- **Reports** — diagnostic reports and clinical notes (radiology, pathology,
  cardiology, etc.), each with an AI-generated plain-language summary.
- **AI Summary** — a narrative overview of your latest panel: what's out of range,
  what changed significantly since last time, and what's worth asking your doctor.
- **Chat** — a persistent side panel to ask questions about your own results. Every
  factual answer is grounded by having Claude query your local data via tool-calling,
  not recalled from memory — it cites the specific values and dates it used.

## Architecture

```
┌─────────────────────────────┐
│  Browser (localhost)        │
│  React SPA: Labs / Trends / │
│  Reports / Chat sidebar     │
└─────────────┬────────────────┘
              │ REST (HTTPS, local only)
┌─────────────▼────────────────────────────────┐
│  FastAPI backend (localhost:8000)             │
│  ├─ Auth: SMART-on-FHIR OAuth2 + PKCE          │
│  ├─ Sync: pulls & normalizes Epic FHIR data     │
│  ├─ SQLite: local, encrypted-at-rest via disk   │
│  ├─ REST API: /labs /trends /reports /summary  │
│  │            /chat /sync                       │
│  └─ LLM orchestrator: Claude + tool-calling     │
│     grounded in the local database              │
└─────────────┬────────────────┬──────────────────┘
              │                │
   Epic FHIR R4 (your health   Anthropic Claude API
   system's Patient Access     (summary + chat)
   API)
```

**Backend**: Python + FastAPI, `httpx` for HTTP, `SQLModel`/SQLite for storage,
`keyring` for OS-level secret storage (refresh tokens are never written to disk in
plaintext).

**Frontend**: React + TypeScript + Vite, Recharts for the Trends chart,
`react-markdown` for rendering the AI summary.

**LLM**: Anthropic Claude API, using tool-calling — the model calls functions like
`get_lab_history`, `get_latest_panel`, and `get_report` to query your actual data
before answering, rather than free-recalling values it might get wrong.

## Epic / MyChart integration

MyChart is Epic's patient portal product — access goes through **Epic on FHIR**,
Epic's SMART-on-FHIR patient-access API, which every Epic-hosted health system
exposes under the U.S. ONC Cures Act Patient Access rule. This app is registered as
a **patient-facing, standalone-launch SMART app** (not a backend/system integration),
meaning:

1. You click "Connect MyChart."
2. Your browser is sent to **your health system's own MyChart login page** — you log
   in there directly. This app never sees or stores your password.
3. You approve read-only access to your own records.
4. Your health system redirects back with a short-lived authorization code.
5. The backend exchanges that code (via a confidential client secret, kept only in
   your local `.env`, never in this repo) for an access token, using PKCE (S256) for
   an extra layer of protection against code interception.
6. The backend uses that token to read `Patient`, `Observation` (labs), `DiagnosticReport`,
   and `DocumentReference` (clinical notes) resources — read-only, nothing is ever
   written back to your medical record.

**Two environments, fully separate credentials and endpoints:**
- **Sandbox** — Epic's public testing environment with synthetic patients, used to
  build and verify this app before touching real data.
- **Production** — your real health system's own FHIR server (a different base URL
  per health system — Epic maintains a public directory of these at
  [open.epic.com/MyApps/endpoints](https://open.epic.com/MyApps/endpoints)), with its
  own client secret. Each health system approves the app to their own instance
  independently, even under the same Epic app registration.

**Why "Read" and "Search" both matter**: Epic grants API access at the level of
specific interactions. `Read` alone only supports fetching one resource by exact ID —
a sync needs `Search` (`?patient=...`) too, since you can't know record IDs in
advance. This app requests both for Observation, DiagnosticReport, and
DocumentReference.

## Setup

### Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your own Epic app credentials + Anthropic key
uvicorn app.main:app --port 8000
```

For production use (a real health system, not the sandbox), Epic requires an
**https** redirect URI. A local self-signed certificate works for this:
```bash
openssl req -x509 -newkey rsa:2048 -keyout certs/localhost-key.pem \
  -out certs/localhost-cert.pem -days 825 -nodes -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
uvicorn app.main:app --port 8000 --ssl-keyfile certs/localhost-key.pem --ssl-certfile certs/localhost-cert.pem
```
Your browser will flag the self-signed cert as untrusted on first visit — expected
for local development; click through it.

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Then open `http://localhost:5173`, click **Connect MyChart**, and log in.

## Registering your own Epic app

To connect this to your own MyChart account, you'll need to register your own app
at [fhir.epic.com](https://fhir.epic.com) (free):

1. Create the app as **Patient-facing / standalone launch**, FHIR R4.
2. Request Incoming API access for `Patient.Read`, `Observation.Read` + `.Search`
   (Labs), `DiagnosticReport.Read` + `.Search` (Results), and `DocumentReference.Read`
   + `.Search` (Clinical Notes).
3. Mark it a **confidential client** (this app has a backend that can hold a secret).
4. Test against the public sandbox first — it works immediately, no approval needed.
5. For production, submit your app for your specific health system's approval (or,
   if you opt into Epic's automatic distribution program for USCDI-compliant apps,
   many health systems' patients can request it directly).

See `PRD_v2.md` for the full requirements/architecture writeup and
`IMPLEMENTATION_PLAN.md` for the phase-by-phase build log, including the exact
issues hit and how they were resolved (scope propagation delays, Read-vs-Search
scoping, the OperationOutcome-in-search-results quirk, etc.).

## Privacy & security

- All lab/report data is stored **locally only**, in a SQLite database on your own
  machine — nothing is synced to a cloud service by this app.
- OAuth refresh tokens are stored in the OS keychain (via `keyring`), not in
  plaintext config files.
- `.env`, TLS certificates, and the local database are all gitignored — never
  committed.
- Data sent to Anthropic's Claude API is limited to what a specific tool call
  returns (e.g. one test's history when asked about it), not a bulk data dump.
- This is a personal-use, single-user application — see [`Terms & Conditions`](./Terms%20&%20Conditions)
  for the full usage terms.

## Status

Actively in development. See `IMPLEMENTATION_PLAN.md` for current phase and
what's still open.
