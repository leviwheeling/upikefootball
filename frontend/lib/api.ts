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
};
