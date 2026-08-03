import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import analytics from "../../backend/data/compiled/upike_play_analytics_2025.json";
import analytics2024 from "../../backend/data/compiled/upike_play_analytics_2024.json";
import { PlayAnalyticsPanel } from "./play-analytics";

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn(async () => ({
    ok: true,
    json: async () => analytics,
  } as Response)));
});

afterEach(() => cleanup());

test("drills from game and player analytics to source-linked snaps", async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const onPlayer = vi.fn();
  render(<QueryClientProvider client={client}><PlayAnalyticsPanel onPlayerSelect={onPlayer} /></QueryClientProvider>);

  expect(await screen.findByText("866")).toBeInTheDocument();
  expect(screen.getByText("Where Scoreboard Points Were Lost")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("tab", { name: "Games" }));
  fireEvent.click(screen.getByRole("button", { name: /Georgetown/ }));
  expect(await screen.findByText("Snap Ledger")).toBeInTheDocument();
  expect(screen.getByText(/93 snaps matched/)).toBeInTheDocument();

  fireEvent.click(screen.getByRole("tab", { name: "Players" }));
  fireEvent.click(screen.getByRole("button", { name: /Xavier Malone/ }));
  expect(onPlayer).toHaveBeenCalledWith("Xavier Malone");
});

test("opens 2024 player totals, game graph, splits, and linked snaps", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => ({
    ok: true,
    json: async () => analytics2024,
  } as Response)));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const onPlayer = vi.fn();
  render(<QueryClientProvider client={client}><PlayAnalyticsPanel season="2024" onPlayerSelect={onPlayer} /></QueryClientProvider>);

  expect(await screen.findByText("959")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("tab", { name: "Players" }));
  fireEvent.click(screen.getByRole("button", { name: /Lee Kirkland/ }));
  expect(screen.getByRole("dialog", { name: /Lee Kirkland 2024-25/ })).toBeInTheDocument();
  expect(screen.getByText("Official Gamebook Totals")).toBeInTheDocument();
  expect(screen.getByText("Game Trend")).toBeInTheDocument();
  expect(screen.getByText("Game Splits")).toBeInTheDocument();
  expect(onPlayer).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Open all linked snaps" }));
  expect(await screen.findByText("Snap Ledger")).toBeInTheDocument();
  expect(screen.getByText(/snaps matched/)).toBeInTheDocument();
});
