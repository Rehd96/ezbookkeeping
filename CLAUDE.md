# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

ezBookkeeping is a self-hosted personal finance app. Single Go binary serves both a JSON API and the compiled Vue frontend. SQLite, MySQL, and PostgreSQL are all supported via the same datastore abstraction.

## Common commands

### Backend (Go 1.26)

```sh
# Run the dev server (requires conf/ezbookkeeping.ini or pass --conf-path)
go run ezbookkeeping.go server run

# All Go tests
go test ./...

# A single package / single test
go test ./pkg/services -run TestAccounts_Create
```

The CLI has subcommands beyond `server`: `database` (schema migrations / maintenance), `userdata` (import/export), `cron`, `security`, `utility`. See `cmd/` and `ezbookkeeping.go`.

### Frontend (Vue 3 + Vite)

```sh
npm install
npm run serve        # dev server
npm run build        # production bundle into dist/
npm run lint         # vue-tsc --noEmit && eslint --fix
npm run test         # vitest run
npx vitest run path/to/file.test.ts   # single file
```

The frontend builds two separate SPAs (`desktop.html`, `mobile.html`) from one source tree — see `vite.config.ts` and the `src/desktop-main.ts` / `src/mobile-main.ts` / `src/index-main.ts` entry points.

### Full builds

`build.sh` (or `build.bat` / `build.ps1`) is the canonical build entry point used by CI. Types: `backend`, `frontend`, `package`, `docker`. Pass `--no-lint` / `--no-test` to skip checks. `RELEASE_BUILD=1` toggles release vs. snapshot.

```sh
./build.sh backend
./build.sh frontend
./build.sh package -o ezbookkeeping.tar.gz
./build.sh docker -t mayswind/ezbookkeeping:dev
```

## Architecture

### Backend layering (`pkg/`)

Requests flow: `cmd/webserver.go` wires Gin routes → `pkg/middlewares` (auth, request id, rate limit) → `pkg/api/*.go` handlers → `pkg/services/*.go` business logic → `pkg/datastore` (XORM-based, dialect-agnostic) → DB. `pkg/models` holds DB entities and request/response DTOs (the `_test.go` files there cover model logic and are the most common unit-test target).

Cross-cutting packages:
- `pkg/core` — context, version, base types shared across layers.
- `pkg/settings` — parses `conf/ezbookkeeping.ini`; almost every subsystem reads from here.
- `pkg/errs` — typed errors that map to API error codes/HTTP statuses.
- `pkg/validators` — custom Gin binding validators (username, currency, amount filters, etc.) registered at startup.
- `pkg/cron` — scheduled jobs (registered in `cmd/cron_jobs.go`).
- `pkg/converters` — third-party file format import/export (CSV, OFX, QIF, GnuCash, Beancount, Camt, MT940, …). Each format is its own subpackage.
- `pkg/exchangerates` — pluggable rate providers; one file per upstream.
- `pkg/duplicatechecker` — in-memory idempotency/rate-limit store (submission deduplication, cron guard, login failure counting); the interface is backed by a single in-memory implementation today but is designed to be replaced.
- `pkg/storage` — pluggable object storage interface (local filesystem, MinIO, WebDAV) used for transaction picture attachments.
- `pkg/mail` — email sending abstraction used by the forgot-password flow.
- `pkg/auth/oauth2` — OIDC / OAuth2 provider integrations for external authentication.
- `pkg/llm` and `pkg/mcp` — LLM client + Model Context Protocol server for AI features.
- `pkg/locales` — server-side translations (separate from the frontend's `src/locales`).

The CLI commands in `cmd/` are *not* the web server's business logic — they share `pkg/services` with it. Adding an admin operation usually means: add a service method, then a thin CLI command and/or API handler that calls it.

### Frontend (`src/`)

- Two SPA bundles: `desktop` (Vuetify-based) and `mobile` (Framework7-based) share `src/components`, `src/stores` (Pinia), `src/lib`, `src/models`, `src/locales`, `src/core`.
- `src/core/` — pure TypeScript types, interfaces, and enums (e.g. `api.ts` defines `ApiResponse<T>` / `ErrorResponse`, `transaction.ts` defines `TransactionType`). No side effects, no axios.
- `src/lib/` — business-logic helpers and the main axios-based API client (`services.ts`). The service layer calls `src/core/api.ts` response types; Pinia stores call service functions.
- View files split: `src/views/desktop/`, `src/views/mobile/`, `src/views/base/` (shared logic / mixins).
- Path alias `@` → `src/` (set in both `vite.config.ts` and `vitest.config.ts`).
- Routing: `src/router/` (vue-router); the desktop/mobile entry points each mount their own router config.
- i18n: vue-i18n with locale JSON in `src/locales/`. Translation progress is tracked per-language and gated by CI (`update-i18n-progress.yml`).

### Configuration

Runtime config lives in `conf/ezbookkeeping.ini`. The same file documents every option inline — when adding a setting, extend that ini file *and* `pkg/settings`. Environment variables can override ini keys (see `pkg/settings`).

### Skill / API tooling

`skills/ezbookkeeping/` ships an "Agent Skill" (a wrapper around `scripts/ebktools.sh` / `.ps1`) so external agents can call the API. Requires `EBKTOOL_SERVER_BASEURL` and `EBKTOOL_TOKEN`.
