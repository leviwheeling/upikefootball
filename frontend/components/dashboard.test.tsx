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
  expect(screen.getByText("2 categories")).toBeInTheDocument();
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
