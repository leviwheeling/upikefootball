import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { Dashboard } from "./dashboard";

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn(async () => ({
    ok: true,
    json: async () => ({
      team: "Pikeville (KY)",
      conference: "Appalachian Athletic Conference",
      default_season: "2025",
      sources: [],
      player_profiles: {
        "Xavier Malone": {
          seasons: [
            { season: "2024", label: "2024-25", games: 2, categories: { Passing: { GP: "2", YDS: "400", TD: "3" } }, metrics: { passing_yards: 400 }, source_url: "https://upikebears.com/sports/football/stats/2024" },
            { season: "2025", label: "2025-26", games: 1, categories: { Passing: { GP: "1", YDS: "3492", TD: "24" } }, metrics: { passing_yards: 3492 }, source_url: "https://naiastats.prestosports.com/team" },
          ],
          career: { games: 3, passing_yards: 3892, completions: 300, pass_attempts: 450, passing_touchdowns: 27, pass_interceptions: 8 },
          primary_metric: { key: "passing_yards", label: "Passing Yards", short: "Pass Yds" },
          honors: [{ label: "NAIA Offensive Player of the Week", url: "https://www.naia.org/player-of-the-week" }],
          scope: "Verified UPIKE cumulative statistics only.",
        },
      },
      seasons: {
        "2025": {
          label: "2025-26", record: "4-6", conference_record: "4-2", region_record: "3-4",
          home: "4-1", away: "0-5", neutral: "0-0", streak: "L1",
          national_rank: "65", aac_rank: "3",
          headline: { "Yds/Game": "462.8", "Pts/Game": "36.5" },
          team_stats: [{ metric: "Scoring", overall: "365", overall_rank: "2nd", conference: "267", conference_rank: "2nd", opponent: "297" }],
          game_log: [{
            date: "Aug 30", opponent: "at Georgetown (Ky.)", score: "L, 34-17",
            game_id: "20250830_dizi", source_url: "https://naiastats.prestosports.com/gamebook",
          }],
          schedule: [],
          appearances: { "Xavier Malone": ["20250830_dizi"] },
          players: {
            Passing: { columns: ["GP", "YDS", "TD"], rows: [{ jersey: "1", player: "Xavier Malone", GP: "10", YDS: "3492", TD: "24" }] },
            Rushing: { columns: ["GP", "YDS"], rows: [{ jersey: "1", player: "Xavier Malone", GP: "10", YDS: "184" }] },
          },
        },
      },
    }),
  } as Response)));
});

afterEach(() => cleanup());

test("opens a source-linked player profile with stats and verified games", async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><Dashboard /></QueryClientProvider>);

  await screen.findByText("Pikeville (KY)", { exact: false });
  fireEvent.click(screen.getByRole("button", { name: /Players 1/ }));
  fireEvent.click(screen.getByRole("button", { name: "Open Xavier Malone profile" }));

  expect(screen.getByRole("dialog", { name: "Xavier Malone" })).toBeInTheDocument();
  expect(screen.getByText("Verified UPIKE Career Totals")).toBeInTheDocument();
  expect(screen.getByText("2 seasons / 3 games")).toBeInTheDocument();
  expect(screen.getByText("3,892")).toBeInTheDocument();
  expect(screen.getByText("Career Trend")).toBeInTheDocument();
  expect(screen.getByText("Analysis")).toBeInTheDocument();
  expect(screen.getByText("Season History")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /NAIA Offensive Player/ })).toHaveAttribute("href", "https://www.naia.org/player-of-the-week");
  expect(screen.getByText("1 verified appearance")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /at Georgetown/ })).toHaveAttribute("href", "https://naiastats.prestosports.com/gamebook");
  fireEvent.click(screen.getByRole("button", { name: "Close player profile" }));
});

test("renders the data-first stat board", async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><Dashboard /></QueryClientProvider>);

  expect(await screen.findByText("Pikeville (KY)", { exact: false })).toBeInTheDocument();
  expect(screen.getByText("462.8")).toBeInTheDocument();
  expect(screen.getByText("Team Statistics")).toBeInTheDocument();
  expect(screen.queryByText(/Every truth/)).not.toBeInTheDocument();
});
