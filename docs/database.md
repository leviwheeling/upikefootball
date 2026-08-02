# Database entity-relationship design

The first migration implements the solid-line vertical slice below. Dashed groups describe the normalized target design for later phases.

```mermaid
erDiagram
  SOURCE_DOCUMENT ||--o{ SEASON : supports
  SOURCE_DOCUMENT ||--o{ SOURCE_PLAYER : contains
  SOURCE_DOCUMENT ||--o{ GAME_SOURCE : contains
  SEASON ||--o{ GAME : schedules
  PLAYER ||--o{ SOURCE_PLAYER : resolves
  PLAYER ||--o{ ROSTER_MEMBERSHIP : has
  TEAM ||--o{ ROSTER_MEMBERSHIP : fields
  SEASON ||--o{ ROSTER_MEMBERSHIP : scopes
  GAME ||--o{ GAME_SOURCE : corroborated_by
  GAME ||--o{ DRIVE : contains
  DRIVE ||--o{ PLAY : contains
  GAME ||--o{ TEAM_GAME_STAT : measures
  GAME ||--o{ PLAYER_GAME_STAT : measures
  PLAYER ||--o{ PLAYER_GAME_STAT : earns
  METRIC_DEFINITION ||--o{ METRIC_VALUE : defines
  CALCULATION_VERSION ||--o{ METRIC_VALUE : produces
  SOURCE_DOCUMENT ||--o{ PROVENANCE_VALUE : supports
  METRIC_VALUE ||--o{ PROVENANCE_VALUE : explains
  SCRAPE_RUN ||--o{ SOURCE_DOCUMENT : retrieves
  SCRAPE_RUN ||--o{ DATA_QUALITY_ISSUE : reports
```

Target domains also include schools, conferences, divisions, teams, seasons, venues, coaches, player aliases, positions, opponents, game periods, scoring events, possessions, participation, starters, penalties, turnovers, timeouts, rankings, standings, awards, reconciliation candidates, entity conflicts, and manual identity decisions.

All source facts carry the source, URL, source record identifier, retrieval time, parser version, and raw-document key. Canonicalization stores the selected fact and rule while retaining all source facts.
