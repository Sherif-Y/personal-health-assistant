# Personal Health Assistant — PRD v2

Status: Draft v2 (supersedes `Personal Health Assistant PRD.pdf`)
Date: 2026-09-20
Owner: Sherif Yehia

## Background

Build a personal health AI assistant with access to MyChart lab results via
Epic's FHIR patient-access API. The app shows trend analytics and tabulated
views of key lab results, and provides an LLM-based chat and summary
capability for the user to understand their own lab history.

## Users

- Single user (Sherif), for personal lab-result tracking. No multi-tenant or
  external-user support in Phase 1–2.

## Pain Points

- **Lack of AI intelligence in standard provider tools.** MyChart shows raw
  results but no trend intelligence, no AI summary, no natural-language Q&A.
- **Fragmented personal health information.** Lab history is scattered across
  visits/panels with no unified longitudinal view.
  (Note: Phase 1 targets a single MyChart account/health system. If labs are
  actually split across multiple *separate* MyChart logins — different health
  systems — that's a Phase 1.5 follow-up, not solved by this version. See
  Open Questions.)

## Goals & Success Metrics

- Can view all historical lab results, grouped and filterable, within the app
  instead of clicking through MyChart's UI.
- Can see a trend chart for any lab metric with 2+ historical data points.
- LLM summary correctly identifies out-of-range results and trend direction
  for the last sync, with zero fabricated values (spot-checked manually).
- Chat answers are always grounded in retrieved data (never a value the tool
  layer didn't return).

## Scope

### Phase 1 — MVP (this PRD's focus)
- Single MyChart account (one Epic-based health system), read-only access to
  the user's own data.
- Local web app (runs on localhost, single user, no auth beyond the Epic
  OAuth login itself).
- Manual "Sync now" trigger to pull latest labs from Epic FHIR.
- Tabulated + grouped lab view with filtering.
- Trend visualization per lab metric.
- LLM-generated summary of latest panel + trends.
- LLM chat scoped to the user's lab data.

### Phase 2
- WhatsApp (or similar) integration for personal querying.
- Multi-modal ingestion: upload results from Excel/images (for labs outside
  the connected MyChart account — this is likely where the "fragmented
  providers" problem actually gets solved, not via multi-FHIR-account OAuth).

### Phase 3
- Packaged App Store application, scaled for other users (multi-tenant auth,
  per-user data isolation, etc. — out of scope for this PRD).

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Browser (localhost)                                     │
│  React SPA: Dashboard | Trends | Summary | Chat sidebar  │
└───────────────────────────┬───────────────────────────────┘
                            │ REST/HTTP (localhost only)
┌───────────────────────────▼───────────────────────────────┐
│  Backend — Python + FastAPI (local process)                │
│  ├─ Auth module                                             │
│  │    SMART-on-FHIR OAuth2 (Authorization Code + PKCE)      │
│  │    against the health system's Epic FHIR endpoint.       │
│  │    Refresh token stored encrypted (OS keychain via       │
│  │    `keyring`, or SQLCipher-encrypted local DB).           │
│  ├─ Sync service                                             │
│  │    Manual "Sync now" trigger → pulls Observation /        │
│  │    DiagnosticReport resources, paginated, going back      │
│  │    10 years on first sync, incremental thereafter.        │
│  │    Splits results into two normalized schemas:            │
│  │    ┌ Numeric labs:                                        │
│  │    │  { loinc_code, display_name, value, unit,            │
│  │    │    reference_range_low/high, collected_at, category }│
│  │    └ Reports (narrative/document-backed results — e.g.    │
│  │       radiology, pathology, cardiology, discharge         │
│  │       summaries): { report_id, report_type, title,        │
│  │       collected_at, narrative_text, source_attachment }   │
│  │       narrative_text extracted from FHIR `conclusion`/    │
│  │       `text.div` where present, else parsed from the      │
│  │       `presentedForm` attachment (PDF/text).               │
│  ├─ Local DB — SQLite, encrypted at rest                     │
│  │    Stores normalized lab + report history, plus sync      │
│  │    metadata. Source of truth for the UI and for LLM tool  │
│  │    calls — the app never queries Epic FHIR live per-req.  │
│  ├─ API layer                                                │
│  │    GET /labs        (tabulated, grouped, filterable)      │
│  │    GET /trends      (time series per LOINC code)          │
│  │    GET /reports     (list, filterable by type/date)        │
│  │    GET /reports/{id} (narrative + summary + original doc) │
│  │    GET /summary     (cached LLM summary, regenerated      │
│  │                       on new sync)                        │
│  │    POST /chat       (LLM chat, tool-calling grounded)      │
│  │    POST /sync       (trigger manual sync)                 │
│  └─ LLM orchestrator                                          │
│       Claude API (Sonnet), tool-calling against the local     │
│       DB — never a raw data dump into the prompt. Tools:      │
│         get_lab_history(loinc_code)                           │
│         get_latest_panel()                                    │
│         get_reference_range(loinc_code)                       │
│         list_reports(report_type?, date_range?)                │
│         get_report(report_id)                                  │
└───────────────────────────┬───────────────────────────────┘
                            │ HTTPS
              ┌─────────────┴──────────────┐
              ▼                            ▼
     Epic FHIR endpoint              Anthropic Claude API
     (health system's patient        (summary generation +
      access API, OAuth2 scopes:      chat, tool-use grounded
      patient/Observation.read,       on local lab data)
      patient/DiagnosticReport.read,
      patient/Patient.read)
```

### Integration detail: MyChart / Epic FHIR

"MyChart" is Epic's patient portal product — there is no generic MyChart API.
Access is via **Epic on FHIR** (SMART-on-FHIR, R4), which every Epic-hosted
health system exposes for patient-directed data access under the ONC Cures
Act Patient Access rule. Practical steps:

1. Register a developer app at `fhir.epic.com` (free), build/test against
   Epic's public sandbox first.
2. Identify the specific health system's production FHIR base URL (each
   Epic customer has its own endpoint; MyChart login redirects there).
3. Request production access with patient-facing read scopes
   (`patient/Observation.read`, `patient/DiagnosticReport.read`,
   `patient/Patient.read`). Because this is a single-patient, read-only,
   non-commercial use case mandated by federal rule, approval is typically
   lighter-weight than "backend system" integrations — but turnaround time
   is still the health system's IT/security team's call, not immediate.
4. OAuth2 Authorization Code + PKCE flow: user logs in with their real
   MyChart credentials on Epic's login page (the app never sees the
   password), backend receives an authorization code, exchanges for
   access/refresh tokens.

### Security & Privacy

- All PHI is stored locally, encrypted at rest (SQLite + SQLCipher or
  equivalent); no PHI is persisted outside the user's machine except:
  - Epic FHIR endpoint (source of truth, user's own data)
  - Anthropic Claude API (for summary/chat processing, via tool-calling —
    only the specific fields a tool call returns are sent, not a bulk dump)
- Anthropic API traffic is not used for model training by default
  (confirm current terms at time of build).
- Refresh tokens stored via OS keychain, not in plaintext config.
- No telemetry/analytics send lab data anywhere else.

## Requirements

| Requirement | Description | Phase |
|---|---|---|
| Integration to MyChart | OAuth2 SMART-on-FHIR against the health system's Epic FHIR endpoint; scopes for Observation/DiagnosticReport/Patient read; encrypted token storage; token refresh handling. | P0 |
| Data Sync & Local Storage | Manual "Sync now" pulls Observation/DiagnosticReport resources; first sync goes back 10 years (paginated), incremental thereafter; normalizes numeric results into the lab schema and narrative/document results into the report schema; stores in encrypted local DB as source of truth for UI and LLM. | P0 |
| Lab Results Visualization | Tabulated view of all *numeric* lab results; grouped by category (e.g. lipid panel, CBC, metabolic panel — via LOINC panel grouping or a simple mapping table); filter by lab/category/date range; visually flag out-of-range values. | P0 |
| Trend Visualization View | Time-series chart per numeric lab metric; filter/select which metrics to chart; overlay reference range band; support comparing multiple metrics. | P0 |
| Diagnostic Reports View | Separate view for report-type results (radiology, pathology, cardiology, discharge summaries, etc.) that aren't discrete numeric values. List grouped by report type/date; each report shows an LLM-generated plain-language summary plus the original narrative/document; not shown in the trend chart. | P0 |
| LLM Summary | Narrative summary of the latest panel: out-of-range values, trend direction vs. prior results, points worth discussing with a doctor. For a diagnostic report, a plain-language summary of that report's findings/impression, grounded strictly in its text. Regenerated on new sync, cached otherwise. | P0 |
| LLM Chat Window | Side chat window for asking questions about lab results *and* diagnostic reports. Tool-calling grounded on local DB (numeric labs + report narratives); conversation history persisted locally; scoped disclaimers (not medical advice). | P0 |
| Security & Privacy | PHI encrypted at rest; local-only storage except Epic FHIR + Anthropic API calls; refresh tokens in OS keychain; no data sent to LLM beyond what a tool call explicitly returns (note: report narratives can be lengthy free text — full report text is sent when summarizing/answering about that specific report). | P0 |
| Non-functional | Runs entirely on localhost in Phase 1 (no external hosting); single-user, no additional auth layer beyond the Epic OAuth login itself. First 10-year sync may take longer and should show progress rather than blocking silently. | P0 |

## System Prompts

### Chat assistant / summary generator (shared persona)

```
You are a personal lab-results assistant for a single user, working only from
their own historical lab data and diagnostic reports retrieved from MyChart
(Epic FHIR).

Rules:
1. Never state a specific lab value, date, trend, or report finding from
   memory. Always call the provided tools (get_lab_history, get_latest_panel,
   get_reference_range, list_reports, get_report) to retrieve the exact data
   before answering a factual question.
2. If a numeric value is outside its reference range, say so explicitly and
   note the direction/magnitude of any change from prior results.
3. For diagnostic reports (radiology, pathology, cardiology, discharge
   summaries, etc.), summarize only what the report text actually states —
   do not infer a diagnosis or finding the report doesn't contain, and do not
   blend a report's narrative with unrelated numeric labs.
4. You are not a doctor. Do not diagnose, recommend medication changes, or
   tell the user to start/stop a treatment. Explain lab values and report
   language in plain, educational terms and suggest discussing concerning
   results with their physician.
5. If asked about data you don't have, say so directly rather than guessing.
6. Be concise. Define medical/lab terminology briefly on first use.
7. Always cite the collection/report date of anything you reference.

When generating a summary:
- For a lab panel: summarize the most recent panel, call out out-of-range
  results, describe notable trends (improving/worsening/stable) versus prior
  results, and list 1-3 points worth raising with a doctor.
- For a diagnostic report: summarize the report's stated findings/impression
  in plain language, preserving any explicit follow-up recommendations the
  report itself makes. Do not speculate beyond the report's text.
```

## Decisions Locked In (from stakeholder review)

- **Account scope:** Single MyChart account / single health system for
  Phase 1. Multi-account aggregation deferred (likely solved by Phase 2's
  Excel/image upload instead of multiple OAuth integrations).
- **Backend stack:** Python + FastAPI.
- **LLM data flow:** Claude API, tool-calling grounded on local DB, no
  redaction needed — user has accepted that lab fields touched by a tool
  call are sent to Anthropic's API for processing.
- **Sync trigger:** Manual "Sync now" button only (no background auto-sync
  in Phase 1).
- **Historical depth:** First sync pulls 10 years of history (paginated),
  incremental syncs thereafter.
- **Report-type results:** Narrative/document-backed results (radiology,
  pathology, cardiology, discharge summaries, etc.) get a dedicated
  Diagnostic Reports view with their own LLM summary, separate from the
  numeric lab table/trend chart. Chat and summary tools cover both.

## Open Questions

- Which health system's MyChart/Epic FHIR endpoint specifically? (Needed to
  register the app and confirm production access turnaround time.)
- Category grouping: use a maintained LOINC-to-panel mapping, or a simpler
  hardcoded category list covering the labs actually present in this
  account?
- Any labs with non-numeric/qualitative results (e.g. positive/negative,
  detected/not detected) that the trend chart needs to handle differently
  from numeric ones, versus being treated as a "report"?
- For diagnostic reports: does this account's Epic FHIR data expose the
  narrative directly (`conclusion`/`text.div`), or mostly as a PDF/text
  attachment (`presentedForm`) that needs parsing? (Determines whether we
  need a PDF-text-extraction step, and possibly OCR for scanned reports.)
- Should the original report document be viewable/downloadable in the app,
  or is the LLM-generated summary + extracted narrative text sufficient for
  Phase 1?
- What report types should we expect to see (radiology, pathology, cardiology
  notes, etc.) — useful for designing the Diagnostic Reports view's grouping.
- Chat conversation persistence: single ongoing thread, or new thread per
  session?

## Appendix: Steps to Obtain MyChart / Epic FHIR Access

"MyChart" is Epic's product — there's no separate MyChart API. Access goes
through **Epic on FHIR**, Epic's SMART-on-FHIR patient-access program. The
type of app you register matters: you want a **Patient-facing / standalone
SMART app** (the user logs in with their own MyChart credentials and
authorizes your app), *not* a "Backend Systems" app (that's for
system-to-system integration and requires representing a registered
organization — heavier vetting, not what a personal single-user app needs).

1. **Confirm your health system is on Epic.** If you log into "MyChart" at
   all, it is — every MyChart instance is Epic. What you need is *which*
   organization (e.g. "Stanford Health Care," "NYU Langone") so you can find
   its specific FHIR endpoint later.

2. **Create a developer account at `fhir.epic.com`** (free). This is Epic's
   developer portal for third-party apps.

3. **Register a new app**, choosing the **Patient-facing / SMART on FHIR
   (standalone launch)** app type, FHIR version R4. You'll provide:
   - App name/description (fine to note it's a personal, single-user app)
   - Company/organization name — for this sandbox/non-production step, your
     own legal name is fine (e.g. "Sherif Yehia" or "Sherif Yehia — Personal
     Project"); no LLC or formal entity needed here. This may get more
     scrutiny at the production step (see friction point below).
   - Redirect URI — for local dev, something like `http://localhost:8000/callback`
   - Scopes: `patient/Observation.read`, `patient/DiagnosticReport.read`,
     `patient/Patient.read`, plus `launch/patient`, `openid`, `fhirUser`,
     and `offline_access` (needed to get a refresh token instead of
     re-logging in every session).

   Registration immediately gives you a **non-production Client ID** you can
   use against Epic's open sandbox (synthetic test patients) — no approval
   needed for this part. Build and test your full OAuth2 Authorization Code
   + PKCE flow and FHIR queries here first.

4. **Identify your organization's specific FHIR base URL.** Epic maintains a
   directory of client organizations and their endpoints on the developer
   portal. You'll need this to point your app at the right place once you
   move past the sandbox. (Tell me your health system's name and I can help
   you track down the right endpoint/registration details.)

5. **Request production access for your specific organization.** This is
   the step outside your control — Epic/the health system reviews the
   request. Because this is a patient-facing, read-only app for the
   patient's *own* data, it's the exact use case the ONC Cures Act Patient
   Access rule protects, which generally supports approval — but the
   review/turnaround time is still up to that organization's IT/security
   team, and can range from quick to several weeks.

   **Known friction point:** some organizations' production app review
   expects a registered legal entity rather than an individual developer,
   even for personal-use patient access apps. If your organization's process
   blocks on this, it's worth calling their patient portal support line and
   asking specifically about "third-party app access to my own MyChart data
   via the Patient Access API" — this is a right under federal rule, and
   support teams that handle portal questions are often better equipped to
   route this than a generic developer-relations inbox.

6. **Go live**: once approved, swap the sandbox Client ID/endpoint for the
   production ones, log in with your real MyChart credentials through the
   OAuth flow, and confirm you can pull real Observation/DiagnosticReport
   data.

**Fallback if production access stalls:** you can start building and fully
testing the entire app (sync, storage, trends, LLM summary/chat) against
Epic's sandbox with synthetic data, so the approval wait doesn't block
development. If a given organization ultimately won't grant individual
developer access, the Phase 2 "upload from Excel/images" path becomes a
manual stopgap for getting your real data in.

## Risks

- **Epic production access timeline** is the biggest schedule risk — sandbox
  development can start immediately, but real data requires the health
  system's approval, which is out of the user's control.
- **LOINC code inconsistency**: the same lab test can appear under slightly
  different LOINC codes across visits/instruments, which can break trend
  continuity if not normalized carefully. More likely over a 10-year window.
- **Reference ranges can vary by lab/instrument** even for the same LOINC
  code — trend charts need to handle a shifting reference band, not assume
  one fixed range.
- **Report parsing reliability**: if narrative reports are only available as
  PDF attachments rather than structured text, extraction quality depends on
  whether they're text-based or scanned images (scanned would need OCR,
  adding complexity and potential summary inaccuracy).
- **First-sync volume**: 10 years of labs + reports from an active patient
  history could be a large initial pull — needs pagination handling and
  should surface progress to the user rather than appearing to hang.
