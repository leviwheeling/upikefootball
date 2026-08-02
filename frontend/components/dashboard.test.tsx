import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { beforeEach, expect, test, vi } from "vitest";
import { Dashboard } from "./dashboard";

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
    const path = String(input);
    const body = path.includes("seasons")
      ? { data: [], meta: { page: 1, page_size: 25, total: 0 } }
      : { data: [], meta: { page: 1, page_size: 100, total: 0 } };
    return { ok: true, json: async () => body } as Response;
  }));
});

test("renders transparent empty states", async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><Dashboard /></QueryClientProvider>);
  expect(screen.getByText("Every season. Every player.")).toBeInTheDocument();
  expect(await screen.findByText(/No games imported yet/)).toBeInTheDocument();
  expect(screen.getAllByText("Access restricted", { selector: "span" })).toHaveLength(2);
});
