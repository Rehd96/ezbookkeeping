# playmetrics

Pull fresher Google Play metrics than the Play Console UI shows (which lags 2–3+
days and never tells you *how* stale it is). Standalone helper — not wired into
the ezbookkeeping binary.

## One-time setup

1. **Play Console → Setup → API access** — link (or create) a Google Cloud project.
2. Create a **service account** in that project. Back in Play Console, grant it
   access with at least *"View app information and download bulk reports"* (add
   the financial-data permission too if you want revenue reports).
3. In the Cloud project, enable **Google Play Developer Reporting API**.
4. Create + download a **JSON key** for the service account.
5. For bulk reports: **Play Console → Download reports** (any tab) shows a bucket
   URI like `gs://pubsite_prod_1234567890`. Pass `pubsite_prod_1234567890` as
   `-bucket`. The service account above already has read access.

If **Play Console → Setup → API access** is missing or its URL bounces you to the
home page, skip it: create the service account in Google Cloud Console instead,
then in **Play Console → Users and permissions → Invite user** add the service
account's email (`...iam.gserviceaccount.com`) and grant it "View app information"
+ "View financial data". That is enough for the `vitals` / `freshness` commands.
The `reports` (GCS bucket) command still needs the API-access project link — use
the browser's *Download reports → Statistics* page for install CSVs otherwise.

Data can take a few hours after account creation to propagate permissions.

## Usage

```sh
export PLAY_SA_KEY=./sa.json
export PLAY_APP=com.example.app

# How stale is each Android vitals metric set right now?
go run ./scripts/playmetrics freshness

# Android vitals (crash rate, ANR rate, error counts) for the last 30 days -> CSV
go run ./scripts/playmetrics vitals -days 30 -out ./playmetrics-out

# Install / rating / crash / review CSV exports for the last 3 months
go run ./scripts/playmetrics reports -bucket pubsite_prod_1234567890 -months 3 -out ./playmetrics-out
```

Flags also read from env: `PLAY_SA_KEY`, `PLAY_APP`, `PLAY_BUCKET`.

## Output

- `vitals_crashRate.csv`, `vitals_anrRate.csv`, `vitals_errorCount.csv` — one row
  per day per version code, UTF-8, ready to diff or chart.
- `reports/stats/...`, `reports/reviews/...` — verbatim Play Console CSV exports.
  **These are UTF-16LE encoded** (Play's format); convert with
  `iconv -f UTF-16LE -t UTF-8` if a tool chokes.

## How stale is Play data, really?

Google documents the bulk CSV exports as: *"Data is captured daily and posted
within 3 to 7 days in monthly CSV files"*, and explicitly advises **"building
systems that don't depend on the exports being updated at a specific time"**
([Play Console Help](https://support.google.com/googleplay/android-developer/answer/6135870)).
So a multi-day lag is the documented product behaviour, not a misconfiguration.

Measured lag by source (same app, same moment):

| Source | Lag |
|---|---|
| Bulk CSV: installs / uninstalls / active devices | ~9 days |
| Play Console UI statistics chart | ~5 days |
| Reporting API — crash/ANR, DAILY | ~3 days |
| Reporting API — errors, DAILY | ~2 days |
| Reporting API — errors, HOURLY | ~12 hours |

**Installs have no faster path.** The Reporting API `v1beta1` discovery document
exposes only `vitals.*` metric sets plus `anomalies` — there is no installs or
active-devices metric set. Install counts exist solely in the GCS bulk exports
and the Console UI, both on the slow batch pipeline. For install/engagement
numbers in hours rather than days, instrument the app itself (Firebase Analytics
or similar); no Play API removes that lag.

## Notes

- Vitals dates are in `America/Los_Angeles` (the API's fixed reporting timezone).
- Empty vitals CSVs (0 rows) usually mean there is genuinely nothing to report:
  no crashes, no ANRs, no error reports. Google also withholds crash/ANR *rates*
  for apps below a minimum user threshold. To tell the two apart, cross-check
  with `errorIssues:search` / `errorReports:search` — if those are empty too, the
  app is simply clean. `freshness` works regardless and is the useful signal
  there: it reports the real data cutoff, which the Console UI hides.
- `latestEndTime` from the API is the **exclusive** end of `[start, end)`. The
  `freshness` command already converts it to the last *complete* datapoint, so
  its output is one period earlier than the raw JSON — that is correct, not a
  discrepancy.
- Install stats are **not** in the Reporting API yet — they only come from the
  GCS bucket (`reports` command).
- Needs outbound HTTPS to `playdeveloperreporting.googleapis.com`,
  `storage.googleapis.com`, and `oauth2.googleapis.com`.
