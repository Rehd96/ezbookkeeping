// Command playmetrics pulls fresher Google Play metrics than the Play Console UI
// shows, straight from Google's APIs, and writes them to CSV files you can open
// or diff.
//
// It covers two independent data sources:
//
//   1. Google Play Developer Reporting API (playdeveloperreporting.googleapis.com)
//      - Android vitals: crash rate, ANR rate, error report counts.
//      - Also reports each metric set's freshness (how stale the data really is),
//        which the Play Console UI never tells you.
//
//   2. The Play Console bulk report bucket on Google Cloud Storage
//      (gs://pubsite_prod_<developer-id>/). CSV exports for installs, ratings,
//      crashes, and reviews. Same data behind Play Console > Download reports.
//
// Setup (one time):
//
//   1. Play Console > Setup > API access: link (or create) a Google Cloud project.
//   2. Create a service account in that project, then in Play Console grant it
//      access with at least "View app information and download bulk reports"
//      (add financial-data permission too if you also want revenue reports).
//   3. In the Cloud project, enable "Google Play Developer Reporting API".
//   4. Create + download a JSON key for the service account.
//   5. For the GCS reports: Play Console > Download reports > (any tab) shows the
//      bucket URI, e.g. gs://pubsite_prod_1234567890. The number after
//      "pubsite_prod_" is your developer id; pass the whole "pubsite_prod_..."
//      as -bucket. The service account above already has read access to it.
//
// Usage:
//
//   go run ./scripts/playmetrics vitals  -key sa.json -app com.example.app [-days 30] [-out ./playmetrics-out]
//   go run ./scripts/playmetrics reports -key sa.json -app com.example.app -bucket pubsite_prod_1234567890 [-months 3] [-out ./playmetrics-out]
//   go run ./scripts/playmetrics freshness -key sa.json -app com.example.app
package main

import (
	"context"
	"encoding/csv"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"golang.org/x/oauth2/jwt"
)

const (
	reportingBase    = "https://playdeveloperreporting.googleapis.com/v1beta1"
	storageBase      = "https://storage.googleapis.com/storage/v1"
	scopeReporting   = "https://www.googleapis.com/auth/playdeveloperreporting"
	scopeStorageRead = "https://www.googleapis.com/auth/devstorage.read_only"
)

// metricSet is one Android vitals metric set in the Reporting API.
type metricSet struct {
	resource   string   // e.g. "crashRateMetricSet"
	metrics    []string // metric ids to request
	dimensions []string // dimensions to break the data down by (some are required by the API)
}

var vitalsSets = []metricSet{
	{"crashRateMetricSet", []string{"crashRate", "userPerceivedCrashRate", "distinctUsers"}, []string{"versionCode"}},
	{"anrRateMetricSet", []string{"anrRate", "userPerceivedAnrRate", "distinctUsers"}, []string{"versionCode"}},
	{"errorCountMetricSet", []string{"errorReportCount", "distinctUsers"}, []string{"reportType", "versionCode"}},
}

func main() {
	if len(os.Args) < 2 {
		usage()
	}

	cmd := os.Args[1]
	fs := newFlags(cmd)
	_ = fs.Parse(os.Args[2:])

	if *flagKey == "" || *flagApp == "" {
		fatalf("both -key and -app are required")
	}
	if err := os.MkdirAll(*flagOut, 0o755); err != nil {
		fatalf("cannot create -out dir: %v", err)
	}

	ctx := context.Background()

	switch cmd {
	case "freshness":
		client := mustClient(ctx, scopeReporting)
		if err := runFreshness(ctx, client, *flagApp); err != nil {
			fatalf("%v", err)
		}
	case "vitals":
		client := mustClient(ctx, scopeReporting)
		if err := runFreshness(ctx, client, *flagApp); err != nil {
			fatalf("%v", err)
		}
		if err := runVitals(ctx, client, *flagApp, *flagDays, *flagOut); err != nil {
			fatalf("%v", err)
		}
	case "reports":
		if *flagBucket == "" {
			fatalf("-bucket is required for the reports command (e.g. pubsite_prod_1234567890)")
		}
		client := mustClient(ctx, scopeStorageRead)
		if err := runReports(ctx, client, *flagBucket, *flagApp, *flagMonths, *flagOut); err != nil {
			fatalf("%v", err)
		}
	default:
		usage()
	}
}

// ---- flags -----------------------------------------------------------------

var (
	flagKey    *string
	flagApp    *string
	flagOut    *string
	flagDays   *int
	flagMonths *int
	flagBucket *string
)

func newFlags(cmd string) *flag.FlagSet {
	fs := flag.NewFlagSet("playmetrics "+cmd, flag.ExitOnError)
	flagKey = fs.String("key", envOr("PLAY_SA_KEY", ""), "path to the service account JSON key")
	flagApp = fs.String("app", envOr("PLAY_APP", ""), "app package name, e.g. com.example.app")
	flagOut = fs.String("out", "./playmetrics-out", "output directory for CSV files")
	flagDays = fs.Int("days", 30, "vitals: number of days back to query")
	flagMonths = fs.Int("months", 3, "reports: number of past months to download (including current)")
	flagBucket = fs.String("bucket", envOr("PLAY_BUCKET", ""), "reports: GCS bucket id, e.g. pubsite_prod_1234567890")
	return fs
}

// ---- auth ----------------------------------------------------------------

func mustClient(ctx context.Context, scopes ...string) *http.Client {
	data, err := os.ReadFile(*flagKey)
	if err != nil {
		fatalf("cannot read key file: %v", err)
	}
	var key struct {
		ClientEmail string `json:"client_email"`
		PrivateKey  string `json:"private_key"`
		TokenURI    string `json:"token_uri"`
		Type        string `json:"type"`
	}
	if err := json.Unmarshal(data, &key); err != nil {
		fatalf("cannot parse key file: %v", err)
	}
	if key.Type != "service_account" || key.ClientEmail == "" || key.PrivateKey == "" {
		fatalf("key file is not a service account JSON key")
	}
	tokenURL := key.TokenURI
	if tokenURL == "" {
		tokenURL = "https://oauth2.googleapis.com/token"
	}
	conf := &jwt.Config{
		Email:      key.ClientEmail,
		PrivateKey: []byte(key.PrivateKey),
		TokenURL:   tokenURL,
		Scopes:     scopes,
	}
	c := conf.Client(ctx)
	c.Timeout = 60 * time.Second
	return c
}

// ---- freshness ---------------------------------------------------------------

// freshnessResponse is the shape of a metric set's `get` response.
type freshnessResponse struct {
	FreshnessInfo struct {
		Freshnesses []struct {
			AggregationPeriod string   `json:"aggregationPeriod"`
			LatestEndTime     dateTime `json:"latestEndTime"`
		} `json:"freshnesses"`
	} `json:"freshnessInfo"`
}

func fetchFreshness(ctx context.Context, client *http.Client, app, resource string) (freshnessResponse, error) {
	var out freshnessResponse
	err := getJSON(ctx, client, fmt.Sprintf("%s/apps/%s/%s", reportingBase, app, resource), &out)
	return out, err
}

func runFreshness(ctx context.Context, client *http.Client, app string) error {
	fmt.Println("=== metric set freshness (latest COMPLETE datapoint) ===")
	for _, ms := range vitalsSets {
		out, err := fetchFreshness(ctx, client, app, ms.resource)
		if err != nil {
			return fmt.Errorf("%s: %w", ms.resource, err)
		}
		for _, f := range out.FreshnessInfo.Freshnesses {
			end := f.LatestEndTime.asTime()
			if end.IsZero() {
				continue
			}
			// FULL_RANGE aggregates the whole window, so only its cutoff is meaningful.
			if f.AggregationPeriod == "FULL_RANGE" {
				fmt.Printf("  %-22s %-10s cutoff %s (%s)\n",
					ms.resource, f.AggregationPeriod, end.Format("2006-01-02 15:04 MST"), humanAge(end))
				continue
			}
			last := latestDataPoint(end, f.AggregationPeriod)
			layout := "2006-01-02"
			if f.AggregationPeriod == "HOURLY" {
				layout = "2006-01-02 15:04 MST"
			}
			fmt.Printf("  %-22s %-10s %s (%s)\n",
				ms.resource, f.AggregationPeriod, last.Format(layout), humanAge(last))
		}
	}
	fmt.Println()
	return nil
}

// dailyFreshness returns the exclusive end date usable as a DAILY query endTime.
// TimelineSpec.endTime is exclusive too, so the API's latestEndTime can be passed
// through directly — floored to midnight, since DAILY rejects an hours component.
func dailyFreshness(ctx context.Context, client *http.Client, app, resource string) (time.Time, error) {
	out, err := fetchFreshness(ctx, client, app, resource)
	if err != nil {
		return time.Time{}, err
	}
	for _, f := range out.FreshnessInfo.Freshnesses {
		if f.AggregationPeriod != "DAILY" {
			continue
		}
		end := f.LatestEndTime.asTime()
		if end.IsZero() {
			break
		}
		y, m, d := end.Date()
		return time.Date(y, m, d, 0, 0, 0, 0, end.Location()), nil
	}
	return time.Time{}, nil
}

// ---- vitals ----------------------------------------------------------------

func runVitals(ctx context.Context, client *http.Client, app string, days int, outDir string) error {
	end := time.Now().In(losAngeles())
	start := end.AddDate(0, 0, -days)

	for _, ms := range vitalsSets {
		rows, err := queryMetricSet(ctx, client, app, ms, start, end)
		if err != nil {
			return fmt.Errorf("%s: %w", ms.resource, err)
		}
		path := filepath.Join(outDir, fmt.Sprintf("vitals_%s.csv", strings.TrimSuffix(ms.resource, "MetricSet")))
		header := append([]string{"date"}, ms.dimensions...)
		header = append(header, ms.metrics...)
		if err := writeCSV(path, header, rows); err != nil {
			return err
		}
		fmt.Printf("wrote %s (%d rows)\n", path, len(rows))
	}
	return nil
}

func queryMetricSet(ctx context.Context, client *http.Client, app string, ms metricSet, start, end time.Time) ([][]string, error) {
	// The API rejects an end date past the metric set's current freshness, so
	// clamp to whatever DAILY data is actually available.
	if fresh, err := dailyFreshness(ctx, client, app, ms.resource); err != nil {
		fmt.Fprintf(os.Stderr, "warning: %s freshness lookup failed, querying anyway: %v\n", ms.resource, err)
	} else if !fresh.IsZero() && fresh.Before(end) {
		end = fresh
	}
	if !end.After(start) {
		return nil, nil
	}

	u := fmt.Sprintf("%s/apps/%s/%s:query", reportingBase, app, ms.resource)

	type dateJSON struct {
		Year  int `json:"year"`
		Month int `json:"month"`
		Day   int `json:"day"`
	}
	body := map[string]any{
		"timelineSpec": map[string]any{
			"aggregationPeriod": "DAILY",
			"startTime":         dateJSON{start.Year(), int(start.Month()), start.Day()},
			"endTime":           dateJSON{end.Year(), int(end.Month()), end.Day()},
		},
		"metrics":    ms.metrics,
		"dimensions": ms.dimensions,
		"pageSize":   1000,
	}

	var rows [][]string
	pageToken := ""
	for {
		if pageToken != "" {
			body["pageToken"] = pageToken
		}
		var out struct {
			Rows []struct {
				StartTime  dateTime `json:"startTime"`
				Dimensions []struct {
					Dimension   string `json:"dimension"`
					StringValue string `json:"stringValue"`
					Int64Value  string `json:"int64Value"`
				} `json:"dimensions"`
				Metrics []struct {
					Metric       string `json:"metric"`
					DecimalValue struct {
						Value string `json:"value"`
					} `json:"decimalValue"`
				} `json:"metrics"`
			} `json:"rows"`
			NextPageToken string `json:"nextPageToken"`
		}
		if err := postJSON(ctx, client, u, body, &out); err != nil {
			return nil, err
		}
		for _, r := range out.Rows {
			byDim := map[string]string{}
			for _, d := range r.Dimensions {
				byDim[d.Dimension] = firstNonEmpty(d.StringValue, d.Int64Value)
			}
			byMetric := map[string]string{}
			for _, m := range r.Metrics {
				byMetric[m.Metric] = m.DecimalValue.Value
			}
			row := []string{r.StartTime.date()}
			for _, name := range ms.dimensions {
				row = append(row, byDim[name])
			}
			for _, name := range ms.metrics {
				row = append(row, byMetric[name])
			}
			rows = append(rows, row)
		}
		if out.NextPageToken == "" {
			break
		}
		pageToken = out.NextPageToken
	}

	sort.Slice(rows, func(i, j int) bool {
		if rows[i][0] != rows[j][0] {
			return rows[i][0] < rows[j][0]
		}
		return rows[i][1] < rows[j][1]
	})
	return rows, nil
}

// ---- bulk reports (GCS) ----------------------------------------------------

func runReports(ctx context.Context, client *http.Client, bucket, app string, months int, outDir string) error {
	wanted := map[string]bool{}
	now := time.Now().UTC()
	for i := 0; i < months; i++ {
		wanted[now.AddDate(0, -i, 0).Format("200601")] = true
	}

	// List everything under stats/ and reviews/, keep files for this app + months.
	var objects []string
	for _, prefix := range []string{"stats/", "reviews/"} {
		names, err := listObjects(ctx, client, bucket, prefix)
		if err != nil {
			return err
		}
		objects = append(objects, names...)
	}

	appToken := strings.ReplaceAll(app, ".", "_")
	downloaded := 0
	for _, name := range objects {
		if app != "" && !strings.Contains(name, app) && !strings.Contains(name, appToken) {
			continue
		}
		if !matchesMonth(name, wanted) {
			continue
		}
		dest := filepath.Join(outDir, filepath.FromSlash(name))
		if err := os.MkdirAll(filepath.Dir(dest), 0o755); err != nil {
			return err
		}
		if err := downloadObject(ctx, client, bucket, name, dest); err != nil {
			return fmt.Errorf("download %s: %w", name, err)
		}
		fmt.Printf("wrote %s\n", dest)
		downloaded++
	}
	if downloaded == 0 {
		fmt.Println("no matching report files found (check -app / -months / bucket access)")
	}
	// Play Console report CSVs are UTF-16LE; note it so nobody is surprised.
	fmt.Println("note: these CSV files are UTF-16LE encoded (Play Console format)")
	return nil
}

func matchesMonth(name string, wanted map[string]bool) bool {
	for ym := range wanted {
		if strings.Contains(name, "_"+ym) {
			return true
		}
	}
	return false
}

func listObjects(ctx context.Context, client *http.Client, bucket, prefix string) ([]string, error) {
	var names []string
	pageToken := ""
	for {
		u := fmt.Sprintf("%s/b/%s/o?prefix=%s&maxResults=1000", storageBase, url.PathEscape(bucket), url.QueryEscape(prefix))
		if pageToken != "" {
			u += "&pageToken=" + url.QueryEscape(pageToken)
		}
		var out struct {
			Items []struct {
				Name string `json:"name"`
			} `json:"items"`
			NextPageToken string `json:"nextPageToken"`
		}
		if err := getJSON(ctx, client, u, &out); err != nil {
			return nil, err
		}
		for _, it := range out.Items {
			names = append(names, it.Name)
		}
		if out.NextPageToken == "" {
			return names, nil
		}
		pageToken = out.NextPageToken
	}
}

func downloadObject(ctx context.Context, client *http.Client, bucket, object, dest string) error {
	u := fmt.Sprintf("%s/b/%s/o/%s?alt=media", storageBase, url.PathEscape(bucket), url.PathEscape(object))
	req, _ := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
		return fmt.Errorf("HTTP %d: %s", resp.StatusCode, strings.TrimSpace(string(b)))
	}
	f, err := os.Create(dest)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = io.Copy(f, resp.Body)
	return err
}

// ---- HTTP helpers --------------------------------------------------------

func getJSON(ctx context.Context, client *http.Client, u string, out any) error {
	req, _ := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
	return doJSON(client, req, out)
}

func postJSON(ctx context.Context, client *http.Client, u string, body, out any) error {
	buf, err := json.Marshal(body)
	if err != nil {
		return err
	}
	req, _ := http.NewRequestWithContext(ctx, http.MethodPost, u, strings.NewReader(string(buf)))
	req.Header.Set("Content-Type", "application/json")
	return doJSON(client, req, out)
}

func doJSON(client *http.Client, req *http.Request, out any) error {
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	data, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("HTTP %d: %s", resp.StatusCode, strings.TrimSpace(string(data)))
	}
	if out == nil {
		return nil
	}
	return json.Unmarshal(data, out)
}

// ---- misc helpers --------------------------------------------------------

// dateTime mirrors google.type.DateTime. Freshness timestamps carry hours and an
// explicit timezone; timeline row start times carry only the date.
type dateTime struct {
	Year     int `json:"year"`
	Month    int `json:"month"`
	Day      int `json:"day"`
	Hours    int `json:"hours"`
	Minutes  int `json:"minutes"`
	TimeZone struct {
		ID string `json:"id"`
	} `json:"timeZone"`
}

func (d dateTime) date() string {
	if d.Year == 0 {
		return ""
	}
	return fmt.Sprintf("%04d-%02d-%02d", d.Year, d.Month, d.Day)
}

// asTime resolves the timestamp in its own timezone (UTC when unset).
func (d dateTime) asTime() time.Time {
	if d.Year == 0 {
		return time.Time{}
	}
	loc := time.UTC
	if d.TimeZone.ID != "" {
		if l, err := time.LoadLocation(d.TimeZone.ID); err == nil {
			loc = l
		}
	}
	return time.Date(d.Year, time.Month(d.Month), d.Day, d.Hours, d.Minutes, 0, 0, loc)
}

// latestDataPoint turns an exclusive freshness end into the start of the last
// complete bucket. The API documents latestEndTime as the exclusive end of
// [start, end), so the newest readable datapoint sits one period earlier.
func latestDataPoint(end time.Time, period string) time.Time {
	if period == "HOURLY" {
		return end.Truncate(time.Hour).Add(-time.Hour)
	}
	y, m, d := end.Date()
	return time.Date(y, m, d, 0, 0, 0, 0, end.Location()).AddDate(0, 0, -1)
}

func humanAge(t time.Time) string {
	d := time.Since(t)
	switch {
	case d < 0:
		return "in the future?"
	case d < 2*time.Hour:
		return fmt.Sprintf("%d min ago", int(d.Minutes()))
	case d < 48*time.Hour:
		return fmt.Sprintf("%dh ago", int(d.Hours()))
	default:
		return fmt.Sprintf("%d days ago", int(d.Hours()/24))
	}
}

func writeCSV(path string, header []string, rows [][]string) error {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	w := csv.NewWriter(f)
	defer w.Flush()
	if err := w.Write(header); err != nil {
		return err
	}
	return w.WriteAll(rows)
}

func losAngeles() *time.Location {
	loc, err := time.LoadLocation("America/Los_Angeles")
	if err != nil {
		return time.UTC
	}
	return loc
}

func firstNonEmpty(vals ...string) string {
	for _, v := range vals {
		if v != "" {
			return v
		}
	}
	return ""
}

func envOr(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}

func usage() {
	fmt.Fprintln(os.Stderr, strings.TrimSpace(`
playmetrics — pull fresher Google Play metrics than the Play Console UI shows

Commands:
  vitals     query Android vitals (crash/ANR/error) via the Developer Reporting API -> CSV
  freshness  just print how stale each vitals metric set currently is
  reports    download install/rating/crash/review CSV exports from the Play GCS bucket

Run "go run ./scripts/playmetrics <command> -h" for flags.
`))
	os.Exit(2)
}

func fatalf(format string, a ...any) {
	fmt.Fprintf(os.Stderr, "error: "+format+"\n", a...)
	os.Exit(1)
}
