# Scraper guide

## Safety policy

- Use a descriptive contact-bearing user agent.
- Consult `robots.txt` before a target URL.
- Apply at least 10 seconds between requests to the same host by default.
- Retry only transient status codes with exponential backoff and jitter.
- Stop on authentication, CAPTCHA, Cloudflare challenge, or a disallow rule.
- Save successful raw responses before parsing and identify them by SHA-256.
- Resume by source URL and content hash; unchanged content is not reparsed unless explicitly requested.

## Adapter contract

`FootballSourceAdapter` exposes season/team discovery and separate schedule, roster, statistics, box-score, drive, play-by-play, rankings, and standings methods. Unsupported methods raise an explicit `NotImplementedError`; they never return invented empty statistics.

`UPIKEAthleticsAdapter` currently implements the verified 2025 SIDEARM cumulative page. `AACAdapter` and `NAIAAdapter` expose only verified discovery entrypoints and fail closed under the current challenge response.

## Parser changes

Add a new parser module when markup semantics change. Keep the old fixture and parser, add the new real fixture, route by source-system indicators, and test both. Never modify a fixture to make a parser test pass.
