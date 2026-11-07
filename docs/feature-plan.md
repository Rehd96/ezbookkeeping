# ezBookkeeping — Personal Feature Plan

Plan for extending ezBookkeeping with budget tracking (modeled on the
"Foglio spese 2026-Medion.ods" spreadsheet) and line-item receipt OCR.

---

## 1. Rewrite vs. fork: decision

Converting ezbk to Python/Node is the worst option, by a wide margin:

- **Size**: `pkg/` alone is dozens of packages — services, datastore (multi-DB
  via XORM), 10+ file-format importers (OFX/QIF/GnuCash/Beancount/Camt/MT940…),
  exchange-rate providers, OAuth/OIDC, 2FA, MCP server, cron, i18n. Realistically
  30–60k lines of Go that all interoperate. A faithful port is months of
  full-time work even for someone fluent in Go *and* the target language.
- You'd inherit the maintenance burden forever — every upstream feature/bugfix
  would need re-porting by hand.
- "I don't know Go" is a much smaller problem than "I now own a fork of a
  finance app in a different language." Go is one of the easier languages to
  read; you can make additive changes (a new API handler + a new Vue view)
  without understanding the whole codebase.

**Rule of thumb**: learning enough Go to add a handler + service method is
~1–2 weekends. Rewriting is ~6+ months. Not close.

### What ezbk already gives you

| Ask | ezbk status |
|---|---|
| Fixed/recurring expenses (`spese fisse`) | **Built-in** — "Scheduled transactions" |
| Salary − fixed = budget | Partial — categories + reports exist; explicit "budget" object doesn't |
| Daily / weekly budget | **Missing** as a first-class concept |
| Weekly ideal vs. actual trend | **Missing** — but the data + chart engine (ECharts) is there |
| Receipt OCR | **Built-in** — "Receipt image recognition" + LLM/MCP integration (`pkg/llm`, `pkg/mcp`) |
| Line-item breakdown (veg/meat/snacks from one receipt) | **Missing** — current OCR likely extracts merchant/total/date, not line items |

Net-new work: **(1) a Budget entity + weekly/daily derivation, (2) extend the
OCR/LLM prompt to return line items mapped to categories**.

### Companion-app fallback

If touching Go really feels like too much, the lowest-friction alternative is
**don't fork — build a companion app**:

- ezbk already exposes a full REST API (and ships
  `skills/ezbookkeeping/scripts/ebktools.sh` to call it).
- Write a small Python/Node service that: (a) reads transactions via the API,
  (b) stores your budget config + line-items in its own DB, (c) renders the
  dashboards you want.
- You keep upgrading ezbk normally. Your custom layer lives beside it.
- Trade-off: the budget UI lives in a separate site, not inside ezbk. Worse
  UX, but zero Go.

---

## 2. Architecture map (the parts you'll actually touch)

```
HTTP request
   │
   ▼
cmd/webserver.go         ← route table: URL → handler
   │
   ▼
pkg/middlewares          ← auth, request-id, rate limit (you won't touch this)
   │
   ▼
pkg/api/<resource>.go    ← THIN handler: parse request → call service → format response
   │
   ▼
pkg/services/<resource>.go ← business logic, the "interesting" code
   │
   ▼
pkg/datastore            ← XORM session per user (multi-tenant via UserDataDB(uid))
   │
   ▼
DB (sqlite/mysql/postgres)

pkg/models/<resource>.go ← THREE kinds of structs in one file:
                            1. DB entity (xorm tags)
                            2. Request DTOs (json/form tags + validator tags)
                            3. Response DTOs + a To...Response() converter

cmd/database.go          ← one SyncStructs(new(YourModel)) line per table; XORM creates/migrates
```

Every CRUD resource follows that exact shape. `transaction_tags` is the
cleanest small example — ~118 lines of model, ~355 of API, ~589 of service.
Read those three files end-to-end once and ~80% of the codebase becomes
pattern recognition.

Frontend mirrors it:

```
src/lib/services.ts      ← axios wrapper per endpoint
src/stores/<feature>.ts  ← Pinia store, caches data
src/views/desktop/...    ← Vuetify views
src/views/mobile/...     ← Framework7 views (separate file, same store)
src/locales/*.json       ← every label goes through vue-i18n
```

---

## 3. Go concepts to focus on (priority order)

You can ignore most of Go. For additive CRUD work you need:

1. **Structs and struct tags** — the only "weird" syntax you'll meet daily.
   `Name string \`xorm:"VARCHAR(64) NOT NULL"\`` is just metadata other libraries
   read via reflection. XORM uses the `xorm:` tag, Gin uses `json:` and
   `binding:`. Copy-paste, don't memorize.
2. **Pointers and `nil`** — `*models.Budget` means "may be nil, must check".
   Almost every service returns `(*Thing, error)`. The pattern
   `if x == nil { return errs.ErrNotFound }` is everywhere.
3. **The `if err != nil { return ..., err }` rhythm** — Go has no exceptions;
   every line that can fail returns an error and you handle it immediately.
   Looks verbose, becomes muscle memory in a day.
4. **Methods on structs** — `func (s *BudgetService) GetByUid(...)` is just
   `class BudgetService: def get_by_uid(self, ...)`. The `(s *BudgetService)`
   receiver is `self`.
5. **Slices and maps** — `[]*models.Budget`, `map[int64]*models.Budget`. Same
   as Python lists/dicts, less magic.
6. **Interfaces (read-only)** — you'll see `core.Context` passed everywhere;
   you don't need to define interfaces, just pass them through.

Skip for now: goroutines, channels, generics, `context.Context` internals,
reflection. None are needed for what you're building.

Realistic ramp: **a long weekend with the Go tour (tour.golang.org) + reading
`transaction_tags.go` files** is enough to start.

---

## 4. Feature 1: Budget — full walkthrough

Mental model of the spreadsheet, mapped to ezbk concepts:

| Spreadsheet | ezbk equivalent | Status |
|---|---|---|
| Row 7 income | `Transaction` with type=income | exists |
| F46:F59 fixed expenses | `Transaction` repeated via `TransactionTemplate` (scheduled) | exists |
| C73 monthly disposable = salary − fixed | **derived** by your new Budget service | new |
| E73 daily, E73*7 weekly | **derived** | new |
| Row 67 ideal cumulative, row 68 actual | computed from existing transactions vs. Budget config | new |

So you store **very little new state**: just a `Budget` row per user per
period (start date, period type, salary amount or "auto-derive", list of
fixed-expense category IDs). Everything else is computed at read time from
existing transaction data.

### Step 1 — DB model

Create `pkg/models/budget.go`:

```go
package models

type BudgetPeriodType byte

const (
    BudgetPeriodMonthly BudgetPeriodType = 1
    BudgetPeriodWeekly  BudgetPeriodType = 2
)

// Budget represents a user's budget configuration
type Budget struct {
    BudgetId         int64            `xorm:"PK"`
    Uid              int64            `xorm:"INDEX(IDX_budget_uid_deleted) NOT NULL"`
    Deleted          bool             `xorm:"INDEX(IDX_budget_uid_deleted) NOT NULL"`
    Name             string           `xorm:"VARCHAR(64) NOT NULL"`
    PeriodType       BudgetPeriodType `xorm:"NOT NULL"`
    // Income source: either a fixed amount (in user's default currency, minor units),
    // or 0 to mean "sum income transactions in this period".
    PlannedIncome    int64            `xorm:"NOT NULL DEFAULT 0"`
    // Comma-separated category IDs treated as "fixed expenses".
    FixedCategoryIds string           `xorm:"VARCHAR(512) NOT NULL DEFAULT ''"`
    StartUnixTime    int64            `xorm:"NOT NULL"`
    CreatedUnixTime  int64
    UpdatedUnixTime  int64
    DeletedUnixTime  int64
}

// --- Request DTOs ---
type BudgetCreateRequest struct {
    Name             string  `json:"name"          binding:"required,notBlank,max=64"`
    PeriodType       byte    `json:"periodType"    binding:"required,oneof=1 2"`
    PlannedIncome    int64   `json:"plannedIncome" binding:"min=0"`
    FixedCategoryIds []int64 `json:"fixedCategoryIds"`
    StartUnixTime    int64   `json:"startUnixTime" binding:"required"`
}

// --- Response DTO ---
type BudgetInfoResponse struct {
    Id               int64   `json:"id,string"`
    Name             string  `json:"name"`
    PeriodType       byte    `json:"periodType"`
    PlannedIncome    int64   `json:"plannedIncome"`
    FixedCategoryIds []int64 `json:"fixedCategoryIds"`
    StartUnixTime    int64   `json:"startUnixTime"`

    // Derived fields, computed on each read:
    DisposableAmount int64 `json:"disposableAmount"`
    DailyBudget      int64 `json:"dailyBudget"`
    WeeklyBudget     int64 `json:"weeklyBudget"`
}

func (b *Budget) ToInfoResponse() *BudgetInfoResponse {
    // category-id parsing helper omitted for brevity
    return &BudgetInfoResponse{
        Id: b.BudgetId, Name: b.Name, PeriodType: byte(b.PeriodType),
        PlannedIncome: b.PlannedIncome, StartUnixTime: b.StartUnixTime,
    }
}
```

Then add **one line** to `cmd/database.go` next to the others:

```go
err = datastore.Container.UserDataStore.SyncStructs(new(models.Budget))
```

XORM creates/migrates the table on next boot — no SQL migration files.

### Step 2 — Service

Create `pkg/services/budgets.go`. Copy the top of `transaction_tags.go`
verbatim (the singleton + `ServiceUsingDB` boilerplate), then:

```go
type BudgetService struct {
    ServiceUsingDB
    ServiceUsingUuid
}

var Budgets = &BudgetService{
    ServiceUsingDB:   ServiceUsingDB{container: datastore.Container},
    ServiceUsingUuid: ServiceUsingUuid{container: uuid.Container},
}

func (s *BudgetService) GetAllByUid(c core.Context, uid int64) ([]*models.Budget, error) {
    if uid <= 0 { return nil, errs.ErrUserIdInvalid }
    var out []*models.Budget
    err := s.UserDataDB(uid).NewSession(c).
        Where("uid=? AND deleted=?", uid, false).Find(&out)
    return out, err
}

func (s *BudgetService) Create(c core.Context, b *models.Budget) error {
    b.BudgetId = s.GenerateUuid(uuid.UUID_TYPE_BUDGET) // add new const
    b.CreatedUnixTime = time.Now().Unix()
    b.UpdatedUnixTime = b.CreatedUnixTime
    _, err := s.UserDataDB(b.Uid).NewSession(c).Insert(b)
    return err
}
```

The **interesting** method is the derivation. Put it in the same file — it
queries the existing `transactions` table:

```go
// ComputeProgress returns ideal-vs-actual for a budget over [start, now].
func (s *BudgetService) ComputeProgress(
    c core.Context, uid int64, b *models.Budget,
) (ideal, actual int64, err error) {

    fixedIds := parseInt64CSV(b.FixedCategoryIds)
    now := time.Now().Unix()

    // 1. Sum planned income (or take fixed PlannedIncome).
    income := b.PlannedIncome
    if income == 0 {
        income, err = s.sumIncomeBetween(c, uid, b.StartUnixTime, now)
        if err != nil { return 0, 0, err }
    }

    // 2. Sum fixed expenses for this period.
    fixed, err := s.sumExpensesByCategories(c, uid, fixedIds,
        b.StartUnixTime, now)
    if err != nil { return 0, 0, err }

    disposable := income - fixed

    // 3. Ideal: linear burn over period length.
    daysElapsed := (now - b.StartUnixTime) / 86400
    daysTotal   := periodDays(b.PeriodType)
    ideal = disposable * daysElapsed / daysTotal

    // 4. Actual: sum *non-fixed* expenses in period.
    actual, err = s.sumExpensesExcludingCategories(c, uid, fixedIds,
        b.StartUnixTime, now)
    return
}
```

The helpers are 5-line XORM queries against the existing `Transaction` table —
copy the pattern from any `Sum`/`Where` call in `pkg/services/transactions.go`.

### Step 3 — API handler

Create `pkg/api/budgets.go` — the file is almost mechanical:

```go
type BudgetsApi struct {
    budgets *services.BudgetService
}
var Budgets = &BudgetsApi{budgets: services.Budgets}

func (a *BudgetsApi) ListHandler(c *core.WebContext) (any, *errs.Error) {
    uid := c.GetCurrentUid()
    budgets, err := a.budgets.GetAllByUid(c, uid)
    if err != nil {
        log.Errorf(c, "[budgets.ListHandler] %s", err.Error())
        return nil, errs.Or(err, errs.ErrOperationFailed)
    }

    out := make([]*models.BudgetInfoResponse, len(budgets))
    for i, b := range budgets {
        resp := b.ToInfoResponse()
        ideal, actual, _ := a.budgets.ComputeProgress(c, uid, b)
        resp.DisposableAmount = ideal // populate derived fields here
        // ...
        out[i] = resp
    }
    return out, nil
}
```

### Step 4 — Wire routes

In `cmd/webserver.go` near line 445, add:

```go
apiV1Route.GET ("/budgets/list.json",   bindApi(api.Budgets.ListHandler))
apiV1Route.POST("/budgets/add.json",    bindApi(api.Budgets.CreateHandler))
apiV1Route.POST("/budgets/modify.json", bindApi(api.Budgets.ModifyHandler))
apiV1Route.POST("/budgets/delete.json", bindApi(api.Budgets.DeleteHandler))
```

Backend done. **Four new files, two edited.**

### Step 5 — Frontend

- `src/lib/services.ts` — add `getBudgets()`, `addBudget()`, etc. (one axios
  call each).
- `src/stores/budgets.ts` — Pinia store wrapping those calls.
- `src/views/desktop/budgets/List.vue` — Vuetify table + an ECharts area chart
  for ideal-vs-actual (use `vue-echarts`, already installed). The "ideal vs
  actual" line is two arrays of points; ECharts handles the rest.
- Mirror in `src/views/mobile/budgets/`.
- Add labels to `src/locales/en.json` (and let users translate later).

---

## 5. Feature 2: Line-item OCR

The `pkg/llm` and `pkg/templates/prompt` directories already exist for receipt
OCR. Don't write OCR from scratch — extend what's there.

**Sequence:**

1. Read the existing receipt prompt template under `pkg/templates/prompt/`.
   Today it likely returns `{merchant, total, date}`.
2. Modify the prompt to ask for line items in JSON:
   ```
   Return JSON: {
     "merchant": "...", "total": ..., "date": "...",
     "items": [{"name": "...", "qty": ..., "unit_price": ..., "total": ...,
                "category": "vegetables|meat|snacks|..."}]
   }
   ```
3. Extend the response model that captures the LLM output to include
   `Items []ReceiptItem`.
4. Storage choice — pick the simpler one first:
   - **Easy**: store `items` as a JSON blob in a new column on
     `TransactionPictureInfo` (or a new `Items string \`xorm:"TEXT"\``).
     Render in the UI. No new table, no aggregation queries.
   - **Powerful**: new `transaction_line_item` table, indexed by transaction
     id + category. Lets you answer "how much on vegetables this month" with
     SQL.

   Start with Easy. Migrate later if you outgrow it.
5. UI: in the transaction detail view, render the items list under the
   receipt thumbnail. Add a small chart "this receipt by category".

The category vocabulary is the part to think about most. Keep it short
(~10 buckets) and stable, otherwise the LLM will invent variants ("veggies"
vs "vegetables") and your aggregations break. Pin the list inside the prompt.

---

## 6. Development plan

| Phase | Goal | Estimated evenings |
|---|---|---|
| 0 | Fork repo, get `go run ezbookkeeping.go server run` + `npm run serve` working locally against SQLite | 1 |
| 1 | Read `transaction_tags` model+service+api+vue front to back. Don't write code, just read. | 1–2 |
| 2 | Backend Budget CRUD (no derivation yet). Test via curl. | 2–3 |
| 3 | Add `ComputeProgress`. Verify numbers match the spreadsheet for one month. | 2 |
| 4 | Vue list view + create/edit form. | 2–3 |
| 5 | ECharts ideal-vs-actual chart. | 1–2 |
| 6 | Read existing `pkg/llm` + receipt prompt. Try extended prompt manually against the LLM provider before coding. | 1 |
| 7 | Persist line items (JSON blob on picture). Render in UI. | 2 |
| 8 | Optional: promote to a real `line_item` table + monthly category aggregation chart. | 3+ |

Total: roughly **3–5 weeks of evenings** for a Go beginner who's already
comfortable with backend concepts. Phase 1 is the highest-leverage step —
skipping it makes phases 2–3 take three times as long.

---

## 7. Two pitfalls to know up-front

1. **Money is `int64` in minor units** everywhere in this codebase
   (cents/centesimi). Never use `float64` for amounts. The spreadsheet uses
   euros; multiply by 100 on the boundary.
2. **`UserDataDB(uid)`** is the multi-tenant entry point — every read/write
   must go through it, never a global `Container.MainDB`. Copy the pattern;
   don't improvise.
