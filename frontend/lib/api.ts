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
  overall_rank: string;
  conference: string;
  conference_rank: string;
  opponent: string;
};
export type PlayerStatRow = { jersey: string; player: string } & Record<string, string>;
export type PlayerCategory = { columns: string[]; rows: PlayerStatRow[] };
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
  sources: Array<{ label: string; path?: string; url?: string }>;
};
export type Page<T> = { data: T[]; meta: PageMeta };

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
};
