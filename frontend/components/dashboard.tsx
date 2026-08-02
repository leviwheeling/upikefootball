"use client";

import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { createColumnHelper, flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  Activity, ArrowUpRight, BarChart3, BookOpen, ChevronDown, Database,
  Gauge, Home, Menu, Search, ShieldCheck, Sparkles, Trophy, Users, X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { api, type Game } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";

const nav = [
  ["Command center", Home], ["Players", Users], ["Game center", Activity],
  ["Leaderboards", Trophy], ["Advanced metrics", Gauge], ["Record book", BookOpen],
  ["Data quality", ShieldCheck],
] as const;

const column = createColumnHelper<Game>();

function SourceBadge({ value }: { value: string }) {
  return <span className="rounded-full border border-sky-400/20 bg-sky-400/10 px-2 py-1 text-[10px] font-bold uppercase tracking-widest text-sky-300">{value}</span>;
}

export function Dashboard() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const seasons = useQuery({ queryKey: ["seasons"], queryFn: api.seasons });
  const games = useQuery({ queryKey: ["games"], queryFn: api.games });
  const players = useQuery({ queryKey: ["players"], queryFn: api.players });
  const gameRows = games.data?.data ?? [];
  const wins = gameRows.filter((game) => game.result === "W").length;
  const scored = gameRows.filter((game) => game.upike_score !== null);
  const points = scored.reduce((sum, game) => sum + (game.upike_score ?? 0), 0);
  const latestSeason = seasons.data?.data[0];
  const metricCards: Array<{
    label: string;
    value: ReactNode;
    note: string;
    Icon: LucideIcon;
  }> = [
    { label: "Imported seasons", value: seasons.data?.meta.total, note: "Observed", Icon: Database },
    { label: "Player identities", value: players.data?.meta.total, note: "Source-keyed", Icon: Users },
    { label: "Games indexed", value: games.data?.meta.total, note: "Source-linked", Icon: BarChart3 },
    { label: "Win rate", value: scored.length ? `${Math.round((wins / scored.length) * 100)}%` : null, note: "Calculated v1", Icon: Trophy },
  ];

  const chart = useMemo(() => [...gameRows]
    .filter((game) => game.played_at && game.upike_score !== null && game.opponent_score !== null)
    .sort((a, b) => String(a.played_at).localeCompare(String(b.played_at)))
    .map((game) => ({
      opponent: game.opponent.split(" ")[0],
      upike: game.upike_score,
      opponentPoints: game.opponent_score,
    })), [gameRows]);

  const columns = useMemo(() => [
    column.accessor("played_at", { header: "Date", cell: (info) => info.getValue() ? new Date(info.getValue()!).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "—" }),
    column.accessor("opponent", { header: "Opponent", cell: (info) => <span className="font-semibold text-slate-100">{info.getValue()}</span> }),
    column.accessor("site", { header: "Site", cell: (info) => <span className="capitalize text-slate-400">{info.getValue()}</span> }),
    column.accessor("result", { header: "Result", cell: (info) => <span className={cn("font-bold", info.getValue() === "W" ? "text-emerald-400" : "text-rose-400")}>{info.getValue() ?? "—"}</span> }),
    column.display({ id: "score", header: "Score", cell: ({ row }) => <span className="tabular-nums">{row.original.upike_score ?? "—"}<span className="px-1 text-slate-600">–</span>{row.original.opponent_score ?? "—"}</span> }),
    column.accessor("source", { header: "Provenance", cell: (info) => <SourceBadge value={info.getValue()} /> }),
  ], []);
  const table = useReactTable({ data: gameRows.slice(0, 6), columns, getCoreRowModel: getCoreRowModel() });
  const isLoading = seasons.isLoading || games.isLoading || players.isLoading;
  const error = seasons.error || games.error || players.error;

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[248px_1fr]">
      <aside className={cn("fixed inset-y-0 left-0 z-50 w-[280px] border-r border-white/10 bg-[#07101d]/95 p-5 backdrop-blur-xl transition-transform lg:static lg:w-auto lg:translate-x-0", mobileOpen ? "translate-x-0" : "-translate-x-full")}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-xl bg-orange font-black text-ink shadow-glow">UP</div>
            <div><p className="font-[var(--font-display)] font-bold leading-tight">FOOTBALL</p><p className="text-[10px] font-bold tracking-[.24em] text-orange">INTELLIGENCE</p></div>
          </div>
          <button onClick={() => setMobileOpen(false)} className="rounded-lg p-2 text-slate-400 lg:hidden" aria-label="Close navigation"><X size={20} /></button>
        </div>
        <p className="mt-10 px-3 text-[10px] font-bold uppercase tracking-[.22em] text-slate-600">Workspace</p>
        <nav className="mt-3 space-y-1" aria-label="Primary navigation">
          {nav.map(([label, Icon], index) => <a key={label} href="#" className={cn("flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition", index === 0 ? "bg-white/10 text-white" : "text-slate-400 hover:bg-white/5 hover:text-white")}><Icon size={17} className={index === 0 ? "text-orange" : ""} />{label}</a>)}
        </nav>
        <Card className="absolute inset-x-5 bottom-5 overflow-hidden p-4">
          <div className="absolute -right-5 -top-6 h-24 w-24 rounded-full bg-orange/10 blur-2xl" />
          <div className="flex items-center gap-2 text-xs font-semibold"><Database size={14} className="text-emerald-400" /> Data foundation</div>
          <p className="mt-2 text-xs leading-5 text-slate-500">Phase 1 · provenance-first import</p>
          <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10"><div className="h-full w-[28%] rounded-full bg-orange" /></div>
        </Card>
      </aside>

      <main className="min-w-0">
        <header className="sticky top-0 z-40 flex h-20 items-center justify-between border-b border-white/10 bg-[#050b14]/75 px-5 backdrop-blur-xl md:px-8">
          <div className="flex items-center gap-3">
            <button onClick={() => setMobileOpen(true)} className="rounded-xl border border-white/10 p-2 lg:hidden" aria-label="Open navigation"><Menu size={20} /></button>
            <div className="hidden items-center gap-2 text-sm text-slate-500 sm:flex"><Home size={14} /><span>/</span><span className="text-slate-200">Command center</span></div>
          </div>
          <div className="flex items-center gap-3">
            <button className="hidden h-10 items-center gap-2 rounded-xl border border-white/10 bg-white/[.03] px-4 text-sm text-slate-400 sm:flex"><Search size={16} /> Search players <kbd className="ml-4 text-[10px] text-slate-600">⌘ K</kbd></button>
            <button className="flex h-10 items-center gap-2 rounded-xl bg-orange px-4 text-sm font-bold text-ink">{latestSeason?.label ?? "Season"}<ChevronDown size={14} /></button>
          </div>
        </header>

        <div className="grid-field p-5 md:p-8 xl:p-10">
          <section className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-[#102541] via-[#0b1c32] to-[#0a1422] p-6 shadow-2xl md:p-10">
            <div className="absolute right-[-8%] top-[-45%] h-[420px] w-[420px] rounded-full border-[60px] border-orange/[.035]" />
            <div className="relative max-w-3xl">
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-orange/20 bg-orange/10 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[.18em] text-orange"><Sparkles size={12} /> Intelligence command center</div>
              <h1 className="font-[var(--font-display)] text-4xl font-bold tracking-[-.045em] text-white md:text-6xl">Every season. Every player.<br /><span className="text-orange">Every truth the data supports.</span></h1>
              <p className="mt-5 max-w-2xl text-sm leading-6 text-slate-400 md:text-base">A source-linked statistical history of UPIKE football, built for transparent analytics—not invented certainty.</p>
            </div>
          </section>

          {error && <Card className="mt-6 border-rose-500/20 bg-rose-500/5 p-4 text-sm text-rose-300">The API is unavailable. Start the backend and seed the verified fixture, then refresh.</Card>}

          <section className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {metricCards.map(({ label, value, note, Icon }) => <Card key={label} className="group p-5 transition hover:-translate-y-0.5 hover:border-orange/25 hover:bg-white/[.055]">
              <div className="flex items-start justify-between"><div className="grid h-10 w-10 place-items-center rounded-xl bg-white/5 text-slate-400 group-hover:bg-orange/10 group-hover:text-orange"><Icon size={19} /></div><ArrowUpRight size={16} className="text-slate-700" /></div>
              <p className="mt-5 text-xs font-semibold uppercase tracking-[.14em] text-slate-500">{label}</p>
              <p className="mt-2 font-[var(--font-display)] text-3xl font-bold text-white">{isLoading ? "···" : value ?? "Unavailable"}</p>
              <p className="mt-2 text-[11px] font-medium text-slate-600">{note}</p>
            </Card>)}
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-[1.5fr_.8fr]">
            <Card className="min-h-[390px] p-5 md:p-6">
              <div className="flex items-start justify-between"><div><p className="text-xs font-bold uppercase tracking-[.18em] text-orange">Scoring profile</p><h2 className="mt-2 font-[var(--font-display)] text-xl font-bold">Points by game</h2></div><span className="rounded-full bg-white/5 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-500">Observed box scores</span></div>
              {chart.length ? <div className="mt-8 h-[280px]" aria-label="UPIKE and opponent points by game"><ResponsiveContainer width="100%" height="100%"><AreaChart data={chart}><defs><linearGradient id="upike" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#ff5a1f" stopOpacity={0.35}/><stop offset="100%" stopColor="#ff5a1f" stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="rgba(148,163,184,.08)" vertical={false}/><XAxis dataKey="opponent" stroke="#64748b" fontSize={10} tickLine={false} axisLine={false}/><YAxis stroke="#64748b" fontSize={10} tickLine={false} axisLine={false}/><Tooltip contentStyle={{background:"#0b1626",border:"1px solid rgba(255,255,255,.1)",borderRadius:12}}/><Area type="monotone" dataKey="upike" stroke="#ff5a1f" strokeWidth={3} fill="url(#upike)"/><Area type="monotone" dataKey="opponentPoints" stroke="#64748b" strokeWidth={2} fill="transparent"/></AreaChart></ResponsiveContainer></div> : <EmptyState label="Score history appears after a verified fixture import." />}
            </Card>

            <Card className="overflow-hidden">
              <div className="border-b border-white/10 p-6"><p className="text-xs font-bold uppercase tracking-[.18em] text-orange">Data confidence</p><h2 className="mt-2 font-[var(--font-display)] text-xl font-bold">Source coverage</h2></div>
              <div className="space-y-5 p-6">
                <Coverage label="UPIKE Athletics" value={latestSeason ? 100 : 0} status="Fixture verified" color="bg-orange" />
                <Coverage label="AAC / PrestoSports" value={0} status="Access restricted" color="bg-slate-600" />
                <Coverage label="NAIA Stats" value={0} status="Access restricted" color="bg-slate-600" />
              </div>
              <div className="mx-6 mb-6 rounded-xl border border-amber-400/15 bg-amber-400/[.06] p-4 text-xs leading-5 text-amber-200/80"><ShieldCheck size={16} className="mb-2 text-amber-300" />Restricted sources are not bypassed. Missing coverage remains explicitly unavailable.</div>
            </Card>
          </section>

          <Card className="mt-6 overflow-hidden">
            <div className="flex items-center justify-between border-b border-white/10 p-5 md:p-6"><div><p className="text-xs font-bold uppercase tracking-[.18em] text-orange">Game index</p><h2 className="mt-2 font-[var(--font-display)] text-xl font-bold">Latest verified results</h2></div><p className="text-sm tabular-nums text-slate-500">{points || "—"} points indexed</p></div>
            <div className="overflow-x-auto">
              {gameRows.length ? <table className="w-full min-w-[760px] text-left text-sm"><thead className="border-b border-white/10 bg-white/[.02] text-[10px] uppercase tracking-[.16em] text-slate-600">{table.getHeaderGroups().map((group) => <tr key={group.id}>{group.headers.map((header) => <th key={header.id} className="px-6 py-4 font-bold">{flexRender(header.column.columnDef.header, header.getContext())}</th>)}</tr>)}</thead><tbody>{table.getRowModel().rows.map((row) => <tr key={row.id} className="border-b border-white/[.06] transition last:border-0 hover:bg-white/[.025]">{row.getVisibleCells().map((cell) => <td key={cell.id} className="px-6 py-4">{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>)}</tr>)}</tbody></table> : <EmptyState label="No games imported yet. Run the seed command to load the verified page." />}
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
}

function EmptyState({ label }: { label: string }) {
  return <div className="grid min-h-[240px] place-items-center p-8 text-center"><div><Database className="mx-auto text-slate-700" /><p className="mt-3 max-w-sm text-sm leading-6 text-slate-500">{label}</p></div></div>;
}

function Coverage({ label, value, status, color }: { label: string; value: number; status: string; color: string }) {
  return <div><div className="mb-2 flex items-center justify-between text-xs"><span className="font-semibold text-slate-300">{label}</span><span className="text-slate-600">{status}</span></div><div className="h-1.5 overflow-hidden rounded-full bg-white/[.07]"><div className={cn("h-full rounded-full", color)} style={{ width: `${value}%` }} /></div></div>;
}
