# MC Everywhere Analyzer Agent

A production analytics agent that monitors Mailchimp's AI connector channels (ChatGPT and Claude), benchmarks performance against QuickBooks, evaluates the impact of the Marketing Analyzer, and delivers a weekly executive report via Slack and GitHub Pages.

**GitHub Repository:** [github.com/deepakp1308/cursor-skills](https://github.com/deepakp1308/cursor-skills)

**Live Report:** [deepakp1308.github.io/cursor-skills/ai-connector-executive-summary.html](https://deepakp1308.github.io/cursor-skills/ai-connector-executive-summary.html)

**PDF Report:** [deepakp1308.github.io/cursor-skills/ai-connector-executive-summary.pdf](https://deepakp1308.github.io/cursor-skills/ai-connector-executive-summary.pdf)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     GitHub Actions Cron (Tuesday 9 AM PT)               │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          agent/main.py                                  │
│                       Pipeline Orchestrator                             │
│                                                                         │
│  1. Execute Queries ──► 2. Validate ──► 3. Analyze ──► 4. Recommend    │
│  5. LLM Evaluate ──► 6. Render HTML/PDF ──► 7. Post to Slack           │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 ▼               ▼               ▼
          GitHub Pages      Slack Channel     Test Suite
          (HTML + PDF)      (Weekly Post)     (38 tests)
```

---

## System Design

### Data Flow

The agent follows a strict linear pipeline with seven stages. Each stage has isolated responsibilities, making it testable and debuggable independently.

```
BigQuery (11 tables)
    │
    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Queries    │────►│  Validation  │────►│   Analysis   │
│  (7 modules, │     │  (data_checks│     │  (metrics,   │
│   ~15 SQL)   │     │  metric_checks│    │  comparisons,│
└──────────────┘     └──────────────┘     │  funnel,     │
                                          │  correlation,│
                                          │  retention)  │
                                          └──────┬───────┘
                                                 │
                          ┌──────────────────────┼──────────────────────┐
                          ▼                      ▼                      ▼
                   ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
                   │Recommendations│   │ LLM Evaluator│     │   Renderer   │
                   │ (threshold-  │──►│ (Claude API)  │────►│ (Jinja2 HTML │
                   │  based rules)│   │  headline +   │     │  + Playwright │
                   └─────────────┘   │  confidence)  │     │  PDF)         │
                                      └──────────────┘     └──────┬───────┘
                                                                   │
                                                    ┌──────────────┼──────────┐
                                                    ▼              ▼          ▼
                                              GitHub Pages    Slack Post   Local PDF
```

### Analysis Modules

The agent runs six analysis modules, each producing a distinct section of the report:

| Module | File | What It Computes | Key Tables |
|--------|------|-----------------|------------|
| **1a. Core Channel** | `queries/core_channel.py` | Scale, growth velocity, user composition, engagement by tier, product attachment, acquisition conversion | `integrations`, `users`, `users_weekly_rollup`, `genai_eligibility`, `customer_journey`, `sms_daily_rollup`, `daily_transactional_sends`, `messaging_outreach_daily_rollup`, `orders` |
| **1b. Marketing Analyzer Impact** | `queries/analytics_agent_impact.py` | Segment/email lift (Connector+Analyzer vs Connector alone), retention by segment behavior, disconnect rates, Standard-to-Premium upgrade rate, free-to-paid conversion | `integrations`, `genai_eligibility`, `tags_segments_daily_rollup`, `daily_email_send_stats`, `churn_details`, `orders` |
| **2. Cohort by Plan Tier** | `queries/cohort_by_plan.py` | WAU, segment creation, automation adoption, SMS by plan tier (Free/Standard/Legacy/Premium) for each channel | `integrations`, `genai_eligibility`, `users_weekly_rollup`, `tags_segments_daily_rollup`, `customer_journey`, `sms_daily_rollup` |
| **3. Customer Segments** | `queries/customer_segments.py` | Industry breakdown, e-commerce level, high-value flag, geography, language distribution | `integrations`, `genai_eligibility` |
| **4. Funnel Analytics** | `queries/funnel.py` | Connection-to-first-action funnel (WAU, email 30d, segment 30d, automation), time-to-value (median days to first email/segment), drop-off identification | `integrations`, `users_weekly_rollup`, `tags_segments_daily_rollup`, `daily_email_send_stats`, `customer_journey` |
| **5. Correlation** | `queries/correlation.py` | Feature-to-conversion lift (which actions predict paid conversion), multi-product stacking effect (WAU by product count) | `integrations`, `users`, `orders`, `tags_segments_daily_rollup`, `daily_email_send_stats`, `customer_journey`, `sms_daily_rollup`, `users_weekly_rollup` |
| **6. Retention Curves** | `queries/retention_curves.py` | Weekly cohort retention (week 0/1/2/4/8/12 post-connection), churn timing analysis (when do users disconnect?) | `integrations`, `users_weekly_rollup` |

### Metric Computation Layer

All derived metrics are computed in `agent/analysis/metrics.py` as pure functions:

| Function | Formula | Example |
|----------|---------|---------|
| `rate(n, d)` | `(n / d) * 100` | `rate(1692, 2479)` = 68.3% |
| `lift(a, b)` | `a / b` | `lift(68.3, 26.7)` = 2.6x |
| `delta(a, b)` | `a - b` | `delta(82.0, 63.0)` = +19.0 pts |
| `pct_reduction(higher, lower)` | `(higher - lower) / higher * 100` | `pct_reduction(1.5, 0.9)` = 40% |
| `disconnect_rate_reduction(non_seg, seg)` | same as `pct_reduction` | 40% lower disconnect |
| `upgrade_multiplier(seg_rate, nonseg_rate)` | `seg_rate / nonseg_rate` | `0.223 / 0.061` = 3.7x |

Additional analysis modules in `agent/analysis/`:
- `comparisons.py` — Structures QBO vs MC and ChatGPT vs Claude comparisons with hardcoded QBO benchmarks
- `funnel_metrics.py` — Computes funnel conversion rates and identifies the biggest drop-off stage
- `correlation_metrics.py` — Ranks feature-to-conversion lifts and computes stacking effect incremental WAU
- `retention_metrics.py` — Computes retention curve percentages and churn window distributions
- `recommendations.py` — Threshold-based rules that generate prioritized recommendations (critical/high/medium)

### Data Validation

Two validation modules run before and after analysis:

**Pre-analysis (`validation/data_checks.py`):**
- Row count minimums (connector users > 1,000)
- Null rate thresholds (< 5% on key fields)
- Data freshness (most recent record within 72 hours)
- Returns a `DataQualityResult` object with pass/warn/fail status

**Post-analysis (`validation/metric_checks.py`):**
- All percentages between 0-100
- All lifts positive
- User counts consistent across sections
- Week-over-week change within 50% bounds (flags anomalies)

If validation fails, the agent includes a warning in the Slack message rather than silently publishing bad data.

### LLM Evaluator

`agent/llm/evaluator.py` sends computed metrics and draft recommendations to Claude (via the Anthropic API) with a structured prompt (`agent/llm/prompts.py`). The LLM:

1. Verifies each recommendation is logically supported by the data
2. Flags anomalous metrics
3. Generates a 2-3 sentence executive headline for the Slack post
4. Assigns confidence levels (high/medium/low) to each recommendation

Falls back to a deterministic summary if the API key is not configured or the call fails.

### Output Rendering

- **HTML** — Jinja2 template (`agent/output/templates/report.html.j2`) renders all analysis results into a styled HTML report matching the executive summary format
- **PDF** — Playwright (headless Chromium) renders the HTML to Letter-sized PDF with print-optimized styles
- **Slack** — Formatted message with executive headline, key metrics, and report link

### Notification

`agent/notify/slack.py` posts to a Slack channel via incoming webhook. The message format:

```
MC Everywhere Analyzer — Weekly Report — [date]

[LLM headline]

Channel Health:
  ChatGPT: [N] connections ([+N]/day) | [X]% WAU
  Claude:  [N] connections ([+N]/day) | [X]% WAU

Marketing Analyzer Impact:
  Segment lift: [X]x | Email lift: [X]x
  Upgrade multiplier: [X]x | Free→Paid: [X]% vs [X]%

Key Segment Insight: [top industry or ecomm finding]
Funnel Alert: [biggest drop-off stage]
Retention Signal: [cohort trend]

Data Quality: [pass/warn status]

View Full Report: [GitHub Pages URL]
```

---

## Project Structure

```
cursor-skills/
├── agent/
│   ├── __init__.py                        # Package marker
│   ├── main.py                            # Pipeline orchestrator (entry point)
│   ├── config.py                          # BQ project, table names, thresholds
│   ├── queries/
│   │   ├── __init__.py                    # run_query() helper
│   │   ├── core_channel.py                # Module 1a: scale, engagement, attachment
│   │   ├── analytics_agent_impact.py      # Module 1b: Marketing Analyzer lift
│   │   ├── cohort_by_plan.py              # Module 2: metrics by plan tier
│   │   ├── customer_segments.py           # Module 3: industry, ecomm, geo
│   │   ├── funnel.py                      # Module 4: connection-to-action funnel
│   │   ├── correlation.py                 # Module 5: feature-to-conversion
│   │   └── retention_curves.py            # Module 6: cohort retention
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── metrics.py                     # All formula functions
│   │   ├── comparisons.py                 # QBO vs MC structuring
│   │   ├── funnel_metrics.py              # Funnel rates + drop-off
│   │   ├── correlation_metrics.py         # Lift ranking + stacking
│   │   ├── retention_metrics.py           # Cohort curves + churn windows
│   │   └── recommendations.py            # Threshold-based recommendation engine
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── data_checks.py                # Row count, nulls, freshness
│   │   └── metric_checks.py              # Rate bounds, consistency, WoW
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── evaluator.py                   # Claude API evaluation
│   │   └── prompts.py                     # Structured evaluation prompt
│   ├── output/
│   │   ├── __init__.py
│   │   ├── html_renderer.py               # Jinja2 HTML generation
│   │   ├── pdf_generator.py               # Playwright PDF generation
│   │   ├── slack_formatter.py             # Slack message formatting
│   │   └── templates/
│   │       └── report.html.j2             # HTML report template
│   └── notify/
│       ├── __init__.py
│       └── slack.py                       # Webhook-based Slack posting
├── tests/
│   ├── conftest.py                        # Shared fixtures
│   ├── unit/
│   │   ├── test_metrics.py                # 17 tests: every formula
│   │   ├── test_data_checks.py            # 5 tests: validation logic
│   │   ├── test_slack_formatter.py        # 2 tests: message formatting
│   │   ├── test_funnel_metrics.py         # 2 tests: funnel rates
│   │   ├── test_correlation_metrics.py    # 2 tests: lift + stacking
│   │   └── test_retention_metrics.py      # 3 tests: cohort curves
│   ├── functional/
│   │   └── test_pipeline.py               # 4 tests: end-to-end with known data
│   ├── eval/
│   │   └── test_llm_eval.py               # 2 tests: LLM fallback structure
│   └── fixtures/
│       └── mock_bq_results.json           # Frozen real data snapshot
├── docs/
│   ├── index.html                         # GitHub Pages landing page
│   ├── ai-connector-executive-summary.html # Latest report
│   └── ai-connector-executive-summary.pdf  # Latest PDF
├── .github/
│   └── workflows/
│       └── weekly-report.yml              # Cron: Tuesday 9 AM PT
├── requirements.txt                       # Python dependencies
├── .gitignore
└── README.md                              # This file
```

---

## Data Sources

All data comes from the `mc-business-intelligence` BigQuery project:

| Table | Dataset | Purpose |
|-------|---------|---------|
| `integrations` | `bi_reporting` | Connector connections, signups, disconnect rates |
| `users` | `bi_reporting` | Plan type, user profiles |
| `users_weekly_rollup` | `bi_reporting` | Weekly Active Users (WAU) |
| `orders` | `bi_reporting` | Paid conversion, upgrade tracking |
| `tags_segments_daily_rollup` | `bi_reporting` | Segment creation activity |
| `daily_email_send_stats` | `bi_reporting` | Email send volume and performance |
| `emails_customer_journey` | `bi_reporting` | Automation / Customer Journey adoption |
| `sms_daily_rollup` | `bi_reporting` | SMS send activity |
| `daily_transactional_sends` | `bi_reporting` | Transactional email (Mandrill) |
| `messaging_outreach_daily_rollup` | `bi_reporting` | WhatsApp outreach |
| `churn_details` | `bi_reporting` | Account churn records |
| `monthly_genai_user_eligibility` | `bi_reporting_beta` | Marketing Analyzer eligibility, plan tier, industry, ecomm level, high-value flag, country, language |

---

## Testing

**38 tests** across three categories:

```
tests/unit/          — 31 tests: formula correctness, validation logic, formatting
tests/functional/    —  4 tests: end-to-end pipeline with known inputs
tests/eval/          —  2 tests: LLM evaluator output structure
tests/fixtures/      — frozen BigQuery results for deterministic testing
```

Run all tests:
```bash
pip install -r requirements.txt
pytest tests/ -v
```

### Test Coverage by Component

| Component | Tests | What's Verified |
|-----------|-------|----------------|
| `metrics.py` | 17 | Every formula: rate, lift, delta, pct_reduction, upgrade_multiplier, etc. with known inputs from the real analysis |
| `data_checks.py` | 5 | Row count bounds, null rate detection, empty data handling, DataQualityResult aggregation |
| `slack_formatter.py` | 2 | Valid message with all fields, graceful handling of missing data |
| `funnel_metrics.py` | 2 | Funnel conversion rates, biggest drop-off identification |
| `correlation_metrics.py` | 2 | Feature lift sorting, stacking incremental calculation |
| `retention_metrics.py` | 3 | Cohort retention rates, churn window distribution, empty cohort handling |
| `test_pipeline.py` | 4 | Recommendation generation, lift consistency, disconnect reduction, upgrade multiplier |
| `test_llm_eval.py` | 2 | Fallback output structure, empty recommendation handling |

---

## Deployment

### GitHub Actions (Automated Weekly)

The workflow at `.github/workflows/weekly-report.yml` runs every Tuesday at 9 AM PT:

1. Checks out the repository
2. Installs Python 3.12 and dependencies (including Playwright + Chromium)
3. Runs all unit, functional, and eval tests
4. Authenticates to GCP with a service account
5. Executes the full agent pipeline (`python -m agent.main`)
6. Commits updated `docs/` files and pushes (triggers GitHub Pages rebuild)
7. Posts summary to Slack

### Required Secrets

Configure in **GitHub repo Settings > Secrets and variables > Actions**:

| Secret | Purpose |
|--------|---------|
| `GCP_SA_KEY` | Service account JSON with BigQuery Data Viewer role on `mc-business-intelligence` |
| `ANTHROPIC_API_KEY` | Claude API key for the LLM evaluator |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL for the target channel |

### Manual Execution

Trigger from the GitHub Actions tab using "Run workflow", or run locally:

```bash
# Ensure GCP credentials are configured (ADC or service account)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
export ANTHROPIC_API_KEY=sk-ant-...
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

python -m agent.main
```

---

## Key Metrics Tracked

### Channel Performance
- Total connections and daily growth rate (ChatGPT vs Claude)
- User composition (paid vs free, existing vs new)
- Weekly Active User rate by channel and plan tier
- GenAI feature engagement rate among eligible users
- Product attachment (Automations, SMS, Transactional Email, WhatsApp)
- New customer acquisition and paid conversion rate

### Marketing Analyzer Impact
- Segment creation lift (Connector+Analyzer vs Connector alone)
- Email send lift
- Per-user volume (avg segment actions, avg emails delivered)
- Connector disconnect rate by segment-creation behavior
- Standard-to-Premium upgrade rate (segmenters vs non-segmenters)
- Free-to-paid conversion (with analyzer vs without)

### Advanced Analysis
- Cohort metrics by plan tier (Free/Standard/Legacy/Premium)
- Industry, e-commerce, high-value, geography, language breakdowns
- Connection-to-action funnel with time-to-value
- Feature-to-conversion correlation lifts
- Multi-product stacking effect on WAU
- Weekly cohort retention curves and churn timing

---

## QBO Benchmark Data

QuickBooks Online comparison data is provided by the QuickBooks product team and hardcoded in `agent/analysis/comparisons.py`:

| QBO Metric | Value |
|------------|-------|
| ChatGPT connections | 4,792 |
| Claude connections | 4,830 |
| ChatGPT daily adds | ~60 (steady) |
| Claude daily adds | 280-440 |
| ChatGPT Omni engagement | 53% |
| Claude Omni engagement | 49% |
| Advanced tier ChatGPT | 73% |
| Advanced tier Claude | 68% |
| Payments attachment | 29% / 27% |
| Payroll attachment | 19% / 17% |
| BillPay attachment | 18% / 16% |

---

## License

Internal use only. Not for external distribution.
