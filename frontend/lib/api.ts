export type PageMeta = { page: number; page_size: number; total: number };
export type Season = { id: string; year: number; label: string; data_completeness: string };
export type Game = {
  id: string;
  season_id: string;
  played_at: string | null;
  opponent: string;
  site: "home" | "away" | "neutral";
  result: "W" | "L" | null;
  upike_score: number | null;
  opponent_score: number | null;
  attendance: number | null;
  source: string;
  source_url: string;
};
export type Player = {
  id: string;
  display_name: string;
  jersey_number: string | null;
  position: string | null;
  source: string;
  source_url: string | null;
};
export type ConferenceStanding = {
  id: string;
  season_id: string;
  conference: string;
  team_name: string;
  conference_wins: number;
  conference_losses: number;
  overall_wins: number;
  overall_losses: number;
  streak: string;
  source: string;
  source_url: string;
};
export type LeaderEntry = {
  id: string;
  season_id: string;
  category: string;
  metric: string;
  player_name: string;
  games_played: number;
  value_text: string;
  value_numeric: number;
  source: string;
  source_url: string;
};
export type Gamebook = {
  id: string;
  season_id: string;
  played_at: string;
  opponent: string;
  upike_score: number;
  opponent_score: number;
  location: string;
  stadium: string;
  attendance: number | null;
  team_stats: Record<string, unknown>;
  drive_count: number;
  source: string;
  source_url: string;
};
export type TeamStatRow = {
  metric: string;
  overall: string;
  aac_overall_rank: string;
  conference: string;
  aac_conference_rank: string;
  opponent: string;
};
export type PlayerStatRow = { jersey: string; player: string } & Record<string, string>;
export type PlayerCategory = { columns: string[]; rows: PlayerStatRow[] };
export type PlayerHistorySeason = {
  season: string;
  label: string;
  games: number;
  categories: Record<string, Record<string, string>>;
  metrics: Record<string, number>;
  source_url: string;
};
export type PlayerProfile = {
  seasons: PlayerHistorySeason[];
  career: Record<string, number> & { games: number };
  primary_metric: { key: string; label: string; short: string };
  honors: Array<{ label: string; url: string }>;
  scope: string;
};
export type GameLogRow = Record<string, string> & {
  date: string;
  opponent: string;
  score: string;
  game_id?: string;
  source_url?: string;
};
export type ScheduleRow = { date: string; opponent: string; result: string; status: string; notes: string };
export type StatBoardSeason = {
  label: string;
  record: string;
  conference_record: string;
  region_record?: string;
  home: string;
  away: string;
  neutral: string;
  streak: string;
  national_rank?: string;
  aac_rank?: string;
  headline?: Record<string, string>;
  team_stats?: TeamStatRow[];
  game_log?: GameLogRow[];
  players?: Record<string, PlayerCategory>;
  appearances?: Record<string, string[]>;
  schedule: ScheduleRow[];
};
export type StatBoard = {
  team: string;
  conference: string;
  default_season: string;
  seasons: Record<string, StatBoardSeason>;
  player_profiles?: Record<string, PlayerProfile>;
  sources: Array<{ label: string; path?: string; url?: string }>;
};
export type AnalyticsAggregate = {
  label: string;
  plays: number;
  graded_plays: number;
  successes: number;
  success_rate: number | null;
  total_yards: number;
  yards_per_play: number | null;
  explosives: number;
  touchdowns: number;
  negative_plays: number;
  turnover_events: number;
};
export type PlayAnalyticsSnap = {
  id: string;
  game_id: string;
  game_snap: number;
  season_snap: number;
  source_play_number: number | null;
  date: string;
  opponent: string;
  source_url: string;
  quarter: number | null;
  drive: number | null;
  clock: string | null;
  context: string | null;
  description: string | null;
  down: number | null;
  distance: number | null;
  yard_line: number | null;
  gain: number | null;
  result: string;
  play_type: string;
  formation: string | null;
  shift: string | null;
  motion: string | null;
  off_play: string | number | null;
  def_front: string | null;
  blitz: string | null;
  coverage: string | null;
  field_zone: string;
  distance_bucket: string;
  success: boolean | null;
  explosive: boolean;
  negative: boolean;
  touchdown: boolean;
  turnover_event: boolean;
  conversion: boolean;
  no_play: boolean;
  players: string[];
  passer: string | null;
  rusher: string | null;
  target: string | null;
  match_confidence: "high" | "medium" | "low" | "unmatched";
  alignment_cost: number | null;
};
export type PlayAnalyticsGame = {
  game_id: string;
  date: string;
  opponent: string;
  result: string;
  upike_score: number | null;
  opponent_score: number | null;
  point_margin: number | null;
  source_url: string;
  source_pdf: string;
  tagged_rows: number;
  linked_rows: number;
  graded_plays: number;
  success_rate: number | null;
  tagged_yards: number;
  yards_per_play: number | null;
  explosives: number;
  negative_plays: number;
  turnover_events: number;
  third_down: { made: number; attempts: number };
  fourth_down: { made: number; attempts: number };
  official_team_stats: Record<string, string | null>;
};
export type PlayAnalyticsPlayer = {
  player: string;
  games: number;
  plays: number;
  pass_attempts: number;
  completions: number;
  passing_yards: number;
  passing_touchdowns: number;
  interceptions: number;
  rush_attempts: number;
  rushing_yards: number;
  rushing_touchdowns: number;
  targets: number;
  receptions: number;
  receiving_yards: number;
  receiving_touchdowns: number;
  explosives: number;
  successful_plays: number;
  official_season_stats: Record<string, Record<string, string>>;
  game_ids: string[];
};
export type PlayAnalytics = {
  season: string;
  label: string;
  generated_from: Record<string, string>;
  definitions: Record<string, string>;
  coverage: {
    tagged_rows: number;
    linked_official_rows: number;
    linked_pct: number;
    high_confidence_rows: number;
    medium_confidence_rows: number;
    low_confidence_rows: number;
    unmatched_rows: number;
    official_offense_events: number;
    games: number;
    players_with_attribution: number;
    roster_players_with_official_stats: number;
  };
  overview: {
    graded_plays: number;
    successes: number;
    success_rate: number;
    total_tagged_yards: number;
    yards_per_graded_play: number;
    explosives: number;
    negative_plays: number;
    touchdowns: number;
    turnover_events: number;
  };
  recommendations: Array<{ type: string; title: string; evidence: string; filter: Record<string, string> }>;
  top_calls: AnalyticsAggregate[];
  review_calls: AnalyticsAggregate[];
  top_formations: AnalyticsAggregate[];
  play_calls: AnalyticsAggregate[];
  formations: AnalyticsAggregate[];
  situations: Record<string, AnalyticsAggregate[]>;
  games: PlayAnalyticsGame[];
  players: PlayAnalyticsPlayer[];
  snaps: PlayAnalyticsSnap[];
};
export type Page<T> = { data: T[]; meta: PageMeta };

const API_URL = process.env.NEXT_PUBLIC_API_URL
  ?? (process.env.NODE_ENV === "development" ? "http://localhost:8000" : "");

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error(`API request failed (${response.status})`);
  return response.json() as Promise<T>;
}

export const api = {
  seasons: () => get<Page<Season>>("/api/seasons"),
  games: () => get<Page<Game>>("/api/games?page_size=100"),
  players: () => get<Page<Player>>("/api/players?page_size=100"),
  standings: () => get<Page<ConferenceStanding>>("/api/standings?season=2025&page_size=100"),
  leaders: () => get<Page<LeaderEntry>>("/api/leaders?season=2025&page_size=200"),
  gamebooks: () => get<Page<Gamebook>>("/api/gamebooks?season=2025&page_size=10"),
  statBoard: () => get<StatBoard>("/api/stat-board"),
  playAnalytics: () => get<PlayAnalytics>("/api/play-analytics"),
};
