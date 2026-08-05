import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { afterEach, expect, test, vi } from "vitest";
import { PracticeStatsPanel } from "./practice-stats";

const dashboard = {
  season_year: 2026,
  overview: {
    plays: 2, attempts: 2, completions: 1, incompletions: 1, completion_pct: 50,
    on_target: 1, positive_reads: 1, negative_reads: 1, positive_timing: 0,
    negative_timing: 0, receiver_drops: 0, checkdowns: 1,
  },
  quarterbacks: [{
    key: "number:7", display_name: "QB #7", quarterback_number: "7", practices: 1,
    plays: 2, attempts: 2, completions: 1, incompletions: 1, completion_pct: 50,
    on_target: 1, positive_reads: 1, negative_reads: 1, positive_timing: 0,
    negative_timing: 0, receiver_drops: 0, checkdowns: 1,
  }],
  practices: [{
    id: "practice-1", season_year: 2026, title: "QB Practice", practice_date: null,
    practice_type: "Quarterbacks", notes: null, source_label: "QBS.xlsx",
    created_at: "2026-08-05T12:00:00Z", updated_at: "2026-08-05T12:00:00Z",
    summary: {
      plays: 2, attempts: 2, completions: 1, incompletions: 1, completion_pct: 50,
      on_target: 1, positive_reads: 1, negative_reads: 1, positive_timing: 0,
      negative_timing: 0, receiver_drops: 0, checkdowns: 1,
    },
    plays: [{
      id: "play-1", sequence: 1, quarterback_number: "7", quarterback_name: null,
      intended_receiver: "12", result: "INCOMPLETE", notes: "Poor read",
      tags: ["Negative read"],
    }],
  }],
};

afterEach(() => cleanup());

test("renders practice analytics and saves an edited play", async () => {
  const fetchMock = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => ({
    ok: true,
    status: init?.method === "PATCH" ? 200 : 200,
    json: async () => init?.method === "PATCH" ? dashboard.practices[0].plays[0] : dashboard,
  } as Response));
  vi.stubGlobal("fetch", fetchMock);
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><PracticeStatsPanel season={2026} /></QueryClientProvider>);

  expect(await screen.findByText("Practice Statistics")).toBeInTheDocument();
  expect(screen.getByText("Quarterback Summary")).toBeInTheDocument();
  expect(screen.getByText("Negative read")).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("Play 1 notes"), { target: { value: "Good read, on target" } });
  fireEvent.click(screen.getAllByRole("button", { name: "Save" })[0]);

  await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(
    expect.stringContaining("/api/practice-plays/play-1"),
    expect.objectContaining({ method: "PATCH" }),
  ));
  const patchCall = fetchMock.mock.calls.find(([, init]) => init?.method === "PATCH");
  expect(String(patchCall?.[1]?.body)).toContain("Good read, on target");
});
