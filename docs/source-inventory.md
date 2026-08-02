# Source inventory

Discovery was performed on 2026-08-02 with a descriptive user agent and a single request per target plus `robots.txt`. Search/open inspection identified public indexed content; direct HTTP checks recorded current retrieval behavior. No authentication, CAPTCHA, or anti-bot control was bypassed.

| Source | Verified public entrypoint | System | Direct HTTP | Useful evidence |
|---|---|---|---|---|
| UPIKE Athletics | `https://upikebears.com/sports/football/stats/2025` | SIDEARM Sports | 200 | 31 server-rendered tables, 2011–2025 season selector, player roster IDs, 10 box-score links, PDF download |
| AAC | `https://aac.prestosports.com/sports/fball/2025-26` | PrestoSports + Cloudflare | 403 challenge | Indexed football releases and historical XML game-book URLs; 10-second crawl delay |
| NAIA Stats | `https://naiastats.prestosports.com/sports/fball/2025-26/conf/Appalachian/standings?jsRendering=true` | PrestoSports + Cloudflare | 403 challenge | Indexed standings, leaders, schedules, and XML-style box-score URLs; 10-second crawl delay |

UPIKE HTML identifies `schedule-cumestats`, SIDEARM assets, structured navigation data, stable roster paths, and `/boxscore.aspx?id=…` game identifiers. Its response is server-rendered; Playwright is not required for the verified parser.

AAC and NAIA advertise `Crawl-Delay: 10` for general agents. Their public pages are indexed and readable through search infrastructure, but this environment's direct request receives `cf-mitigated: challenge`. The application records that as a blocked scrape run and stops. It does not execute or work around the challenge.

The raw `robots.txt` captures are retained under `discovery/raw/`. Ephemeral challenge pages and cookies are not committed; their status and response indicators are summarized in the discovery report.
