"use client";

import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { Bar, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, type PlayerCategory, type PlayerProfile, type StatBoardSeason } from "@/lib/api";
import { cn } from "@/lib/utils";
import { PlayAnalyticsPanel } from "@/components/play-analytics";
import { PracticeStatsPanel } from "@/components/practice-stats";

type BoardView = "team" | "games" | "players" | "plays" | "practice" | "schedule";

const recordFields = [
  ["Overall", "record"], ["AAC", "conference_record"], ["Region", "region_record"],
  ["Home", "home"], ["Away", "away"], ["Neutral", "neutral"], ["Streak", "streak"],
] as const;

const gameColumns = [
  ["date", "Date"], ["opponent", "Opponent"], ["score", "Score"], ["yds", "Yds"],
  ["pass", "Pass"], ["c_a", "C-A"], ["comp_pct", "Comp%"], ["rush", "Rush"],
  ["rush_att", "R Att"], ["yards_per_rush", "Y/R"], ["int", "INT"], ["fum", "Fum"],
  ["tackles", "Tkl"], ["sacks", "Sack"], ["penalty_yards", "Pen Yds"], ["possession", "TOP"],
] as const;

export function Dashboard() {
  const boardQuery = useQuery({ queryKey: ["stat-board"], queryFn: api.statBoard });
  const [seasonKey, setSeasonKey] = useState("2025");
  const [view, setView] = useState<BoardView>("team");
  const [playerCategory, setPlayerCategory] = useState("Passing");
  const [selectedPlayer, setSelectedPlayer] = useState<string | null>(null);
  const closePlayer = useCallback(() => setSelectedPlayer(null), []);
  const board = boardQuery.data;
  const season = board?.seasons[seasonKey];

  useEffect(() => {
    if (!season || season.team_stats?.length) return;
    if (seasonKey === "2026" && !["practice", "schedule"].includes(view)) setView("practice");
    else if (seasonKey !== "2026" && view !== "schedule") setView("schedule");
  }, [season, seasonKey, view]);

  if (boardQuery.isLoading) return <BoardLoading />;
  if (boardQuery.error || !board || !season) return <BoardError />;

  const playerRows = season.players?.[playerCategory];
  const playerCount = season.players
    ? new Set(Object.values(season.players).flatMap((category) => category.rows.map((row) => row.player))).size
    : 0;

  function selectSeason(key: string) {
    setSeasonKey(key);
    setSelectedPlayer(null);
    const next = board!.seasons[key];
    if (key === "2026") setView("practice");
    else if (!next.team_stats?.length) setView("schedule");
    else if (
      (view === "players" && !next.players)
      || (view === "plays" && !["2024", "2025"].includes(key))
      || view === "practice"
    ) setView("team");
  }

  return (
    <>
    <main className="min-h-screen bg-[#05080e] text-slate-100">
      <header className="sticky top-0 z-50 border-b border-white/10 bg-[#05080e]/95 backdrop-blur-xl">
        <div className="mx-auto flex max-w-[1800px] flex-wrap items-center justify-between gap-4 px-4 py-4 md:px-7">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-md bg-orange font-black text-[#090b0f]">UP</div>
            <div><p className="text-sm font-black uppercase tracking-[.14em]">UPIKE Football</p><p className="text-[10px] font-bold uppercase tracking-[.22em] text-slate-500">Stat Board</p></div>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(board.seasons).map(([key, item]) => (
              <button key={key} onClick={() => selectSeason(key)} className={cn("rounded-md border px-3 py-2 text-xs font-bold tabular-nums transition", seasonKey === key ? "border-orange bg-orange text-[#090b0f]" : "border-white/10 bg-white/[.03] text-slate-400 hover:border-white/25 hover:text-white")}>{item.label}</button>
            ))}
            <form action="/logout" method="post"><button type="submit" className="rounded-md border border-white/10 bg-white/[.03] px-3 py-2 text-xs font-bold text-slate-500 transition hover:border-orange/40 hover:text-orange">Sign out</button></form>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-[1800px] px-4 py-5 md:px-7 md:py-7">
        <section className="flex flex-col justify-between gap-4 border-b border-white/10 pb-5 lg:flex-row lg:items-end">
          <div><p className="text-[10px] font-bold uppercase tracking-[.2em] text-orange">{board.conference}</p><h1 className="mt-1 text-3xl font-black tracking-[-.04em] md:text-4xl">{board.team} <span className="text-slate-600">/</span> {season.label}</h1></div>
          <div className="flex gap-2">
            {season.national_rank && <RankChip label="NAIA" value={`#${season.national_rank}`} />}
            {season.aac_rank && <RankChip label="AAC" value={`#${season.aac_rank}`} />}
          </div>
        </section>

        <section className="mt-4 grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-white/10 bg-white/10 sm:grid-cols-4 xl:auto-cols-fr xl:grid-flow-col xl:grid-cols-none">
          {recordFields.map(([label, field]) => season[field] !== undefined && <RecordCell key={field} label={label} value={String(season[field])} />)}
        </section>

        {season.headline && <section className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4 xl:grid-cols-8">
          {Object.entries(season.headline).map(([label, value]) => <MetricCell key={label} label={label} value={value} negative={label.includes("Allowed")} />)}
        </section>}

        <nav className="mt-6 flex gap-1 overflow-x-auto border-b border-white/10" aria-label="Statistics views">
          {season.team_stats?.length ? <ViewButton active={view === "team"} onClick={() => setView("team")}>Team Stats <Count>{season.team_stats.length}</Count></ViewButton> : null}
          {season.game_log?.length ? <ViewButton active={view === "games"} onClick={() => setView("games")}>Game Log <Count>{season.game_log.length}</Count></ViewButton> : null}
          {season.players ? <ViewButton active={view === "players"} onClick={() => setView("players")}>Players <Count>{playerCount}</Count></ViewButton> : null}
          {["2024", "2025"].includes(seasonKey) ? <ViewButton active={view === "plays"} onClick={() => setView("plays")}>Play Analytics <Count>{seasonKey === "2024" ? 959 : 866}</Count></ViewButton> : null}
          {seasonKey === "2026" ? <ViewButton active={view === "practice"} onClick={() => setView("practice")}>Practice Stats</ViewButton> : null}
          <ViewButton active={view === "schedule"} onClick={() => setView("schedule")}>Schedule <Count>{season.schedule.length}</Count></ViewButton>
        </nav>

        <section className="mt-4">
          {view === "team" && season.team_stats && <TeamStatsTable season={season} />}
          {view === "games" && season.game_log && <GameLogTable season={season} />}
          {view === "players" && season.players && <PlayersTable categories={season.players} selected={playerCategory} onSelect={setPlayerCategory} onPlayerSelect={setSelectedPlayer} />}
          {view === "plays" && ["2024", "2025"].includes(seasonKey) && <PlayAnalyticsPanel season={seasonKey} onPlayerSelect={setSelectedPlayer} />}
          {view === "practice" && seasonKey === "2026" && <PracticeStatsPanel season={2026} />}
          {view === "schedule" && <ScheduleTable season={season} />}
        </section>
      </div>
    </main>
    {selectedPlayer && season.players && <PlayerDrawer playerName={selectedPlayer} season={season} profile={board.player_profiles?.[selectedPlayer]} onClose={closePlayer} />}
    </>
  );
}

function TeamStatsTable({ season }: { season: StatBoardSeason }) {
  return <DataPanel title="Team Statistics" subtitle={`${season.label} / Overall, conference, and opponent`}>
    <table className="stat-table min-w-[850px]"><thead><tr><th>Metric</th><th>Overall</th><th>AAC Overall Rank</th><th>Conference</th><th>AAC Conference Rank</th><th>Opponent</th></tr></thead><tbody>{season.team_stats!.map((row) => <tr key={row.metric}><td className="metric-name">{row.metric}</td><td>{row.overall}</td><td><RankValue value={row.aac_overall_rank} /></td><td>{row.conference}</td><td><RankValue value={row.aac_conference_rank} /></td><td className="text-slate-500">{row.opponent}</td></tr>)}</tbody></table>
  </DataPanel>;
}

function GameLogTable({ season }: { season: StatBoardSeason }) {
  return <DataPanel title="Game Log" subtitle={`${season.game_log!.length} games`}>
    <table className="stat-table min-w-[1450px]"><thead><tr>{gameColumns.map(([, label]) => <th key={label}>{label}</th>)}</tr></thead><tbody>{season.game_log!.map((row) => <tr key={`${row.date}-${row.opponent}`} className={row.score.startsWith("W") ? "win-row" : "loss-row"}>{gameColumns.map(([key]) => <td key={key} className={key === "opponent" ? "metric-name" : key === "score" ? "font-black" : ""}>{row[key]}</td>)}</tr>)}</tbody></table>
  </DataPanel>;
}

function PlayersTable({ categories, selected, onSelect, onPlayerSelect }: { categories: Record<string, PlayerCategory>; selected: string; onSelect: (value: string) => void; onPlayerSelect: (value: string) => void }) {
  const category = categories[selected] ?? Object.values(categories)[0];
  const currentName = categories[selected] ? selected : Object.keys(categories)[0];
  return <>
    <div className="mb-3 flex gap-1 overflow-x-auto">{Object.entries(categories).map(([name, item]) => <button key={name} onClick={() => onSelect(name)} className={cn("whitespace-nowrap rounded-md border px-3 py-2 text-xs font-bold", currentName === name ? "border-orange bg-orange/10 text-orange" : "border-white/10 text-slate-500 hover:text-white")}>{name.replace(" Statistics", "")} <Count>{item.rows.length}</Count></button>)}</div>
    <DataPanel title={currentName} subtitle={`${category.rows.length} player rows`}>
      <table className="stat-table min-w-max"><thead><tr><th>#</th><th>Player</th>{category.columns.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{category.rows.map((row, index) => <tr key={`${row.jersey}-${row.player}-${index}`}><td className="text-slate-600">{row.jersey}</td><td className="metric-name min-w-[190px]"><button className="player-link" onClick={() => onPlayerSelect(row.player)} aria-label={`Open ${row.player} profile`}>{row.player}<span aria-hidden="true">›</span></button></td>{category.columns.map((column) => <td key={column}>{row[column] ?? "-"}</td>)}</tr>)}</tbody></table>
    </DataPanel>
  </>;
}

function PlayerDrawer({ playerName, season, profile, onClose }: { playerName: string; season: StatBoardSeason; profile?: PlayerProfile; onClose: () => void }) {
  const statGroups = Object.entries(season.players ?? {}).flatMap(([name, category]) => {
    const row = category.rows.find((item) => item.player === playerName);
    return row ? [{ name, columns: category.columns, row }] : [];
  });
  const jersey = statGroups[0]?.row.jersey ?? "-";
  const appearanceIds = new Set(season.appearances?.[playerName] ?? []);
  const games = (season.game_log ?? []).filter((game) => game.game_id && appearanceIds.has(game.game_id));
  const appearanceLabel = `${games.length} verified ${games.length === 1 ? "appearance" : "appearances"}`;
  const careerCards = profile ? getCareerCards(profile) : [];
  const analysis = profile ? getPlayerAnalysis(profile) : [];

  useEffect(() => {
    const handleKey = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    document.addEventListener("keydown", handleKey);
    document.body.style.overflow = "hidden";
    return () => { document.removeEventListener("keydown", handleKey); document.body.style.overflow = ""; };
  }, [onClose]);

  return <div className="player-drawer-layer" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <aside className="player-drawer" role="dialog" aria-modal="true" aria-labelledby="player-drawer-title">
      <header className="player-drawer-header"><div><p className="text-[10px] font-black uppercase tracking-[.18em] text-orange">#{jersey} / {season.label}</p><h2 id="player-drawer-title" className="mt-1 text-3xl font-black tracking-[-.035em]">{playerName}</h2></div><button onClick={onClose} className="player-drawer-close" aria-label="Close player profile">×</button></header>
      <div className="player-drawer-body">
        {profile ? <>
          <section><div className="drawer-section-title"><h3>Verified UPIKE Career Totals</h3><span>{profile.seasons.length} seasons / {profile.career.games} games</span></div><div className="career-total-grid">{careerCards.map((card) => <div key={card.label}><span>{card.label}</span><strong>{card.value}</strong></div>)}</div><p className="drawer-scope">{profile.scope}</p></section>
          <section className="mt-7"><div className="drawer-section-title"><h3>Career Trend</h3><span>{profile.primary_metric.label}</span></div><PlayerTrendChart profile={profile} /></section>
          <section className="mt-7"><div className="drawer-section-title"><h3>Analysis</h3><span>Calculated from verified totals</span></div><div className="analysis-grid">{analysis.map((item) => <div key={item.label}><span>{item.label}</span><p>{item.text}</p></div>)}</div></section>
          {profile.honors.length ? <section className="mt-7"><div className="drawer-section-title"><h3>Honors & Context</h3><span>{profile.honors.length} source-linked</span></div><div className="honor-list">{profile.honors.map((honor) => <a key={honor.label} href={honor.url} target="_blank" rel="noreferrer"><span>{honor.label}</span><b aria-hidden="true">↗</b></a>)}</div></section> : null}
          <section className="mt-7"><div className="drawer-section-title"><h3>Season History</h3><span>{profile.seasons.length} verified seasons</span></div><div className="history-season-list">{profile.seasons.map((item, index) => <details key={item.season} open={index === profile.seasons.length - 1 ? true : undefined}><summary><span><b>{item.label}</b><small>{item.games} games</small></span><strong>{formatMetric(item.metrics[profile.primary_metric.key] ?? 0)} {profile.primary_metric.short}</strong></summary><div className="history-season-body"><a href={item.source_url} target="_blank" rel="noreferrer" className="history-source-link">Official cumulative statistics ↗</a>{Object.entries(item.categories).map(([categoryName, stats]) => <div key={categoryName} className="drawer-stat-group"><p>{categoryName.replace(" Statistics", "")}</p><div className="drawer-stat-grid">{Object.entries(stats).map(([label, value]) => <div key={label}><span>{label}</span><strong>{value || "-"}</strong></div>)}</div></div>)}</div></details>)}</div></section>
        </> : <section><div className="drawer-section-title"><h3>Season Statistics</h3><span>{statGroups.length} categories</span></div><div className="space-y-3">{statGroups.map((group) => <div key={group.name} className="drawer-stat-group"><p>{group.name.replace(" Statistics", "")}</p><div className="drawer-stat-grid">{group.columns.map((column) => <div key={column}><span>{column}</span><strong>{group.row[column] ?? "-"}</strong></div>)}</div></div>)}</div></section>}
        <section className="mt-7"><div className="drawer-section-title"><h3>Games Played</h3><span>{appearanceLabel}</span></div><div className="overflow-hidden rounded-lg border border-white/10">{games.map((game) => <a key={game.game_id} href={game.source_url} target="_blank" rel="noreferrer" className="drawer-game-row"><span className="text-slate-500">{game.date}</span><strong>{game.opponent}</strong><span className={game.score.startsWith("W") ? "text-emerald-300" : "text-rose-300"}>{game.score}</span><span aria-hidden="true" className="text-slate-600">↗</span></a>)}</div></section>
      </div>
    </aside>
  </div>;
}

function formatMetric(value: number): string {
  return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(1);
}

function getCareerCards(profile: PlayerProfile): Array<{ label: string; value: string }> {
  const c = profile.career;
  const base = [{ label: "Games", value: formatMetric(c.games) }];
  switch (profile.primary_metric.key) {
    case "passing_yards":
      return [...base, { label: "Passing Yards", value: formatMetric(c.passing_yards) }, { label: "Completions", value: formatMetric(c.completions) }, { label: "Pass TD", value: formatMetric(c.passing_touchdowns) }, { label: "Completion %", value: c.pass_attempts ? `${((c.completions / c.pass_attempts) * 100).toFixed(1)}%` : "-" }, { label: "INT", value: formatMetric(c.pass_interceptions) }];
    case "all_purpose_yards":
      return [...base, { label: "All-Purpose Yards", value: formatMetric(c.all_purpose_yards) }, { label: "Rushing Yards", value: formatMetric(c.rushing_yards) }, { label: "Receiving Yards", value: formatMetric(c.receiving_yards) }, { label: "Receptions", value: formatMetric(c.receptions) }, { label: "Total TD", value: formatMetric(c.rushing_touchdowns + c.receiving_touchdowns + c.kick_return_touchdowns + c.punt_return_touchdowns) }];
    case "rushing_yards":
      return [...base, { label: "Rushing Yards", value: formatMetric(c.rushing_yards) }, { label: "Attempts", value: formatMetric(c.rushing_attempts) }, { label: "Rush TD", value: formatMetric(c.rushing_touchdowns) }, { label: "Yards / Carry", value: c.rushing_attempts ? (c.rushing_yards / c.rushing_attempts).toFixed(1) : "-" }];
    case "receiving_yards":
      return [...base, { label: "Receiving Yards", value: formatMetric(c.receiving_yards) }, { label: "Receptions", value: formatMetric(c.receptions) }, { label: "Receiving TD", value: formatMetric(c.receiving_touchdowns) }, { label: "Yards / Catch", value: c.receptions ? (c.receiving_yards / c.receptions).toFixed(1) : "-" }];
    case "tackles":
      return [...base, { label: "Total Tackles", value: formatMetric(c.tackles) }, { label: "Solo", value: formatMetric(c.solo_tackles) }, { label: "TFL", value: formatMetric(c.tackles_for_loss) }, { label: "Sacks", value: formatMetric(c.sacks) }, { label: "INT", value: formatMetric(c.defensive_interceptions) }];
    case "return_yards":
      return [...base, { label: "Return Yards", value: formatMetric(c.return_yards) }, { label: "Kick Returns", value: formatMetric(c.kick_returns) }, { label: "Punt Returns", value: formatMetric(c.punt_returns) }, { label: "Return TD", value: formatMetric(c.kick_return_touchdowns + c.punt_return_touchdowns) }];
    case "punt_yards":
      return [...base, { label: "Punt Yards", value: formatMetric(c.punt_yards) }, { label: "Points", value: formatMetric(c.points) }];
    default:
      return [...base, { label: "Points", value: formatMetric(c.points) }, { label: "FG Made", value: formatMetric(c.field_goals_made) }, { label: "Extra Points", value: formatMetric(c.extra_points_made) }];
  }
}

function getPlayerAnalysis(profile: PlayerProfile): Array<{ label: string; text: string }> {
  const key = profile.primary_metric.key;
  const recorded = profile.seasons.filter((item) => Math.abs(item.metrics[key] ?? 0) > 0);
  const peak = recorded.length
    ? recorded.reduce((best, item) => (item.metrics[key] ?? 0) > (best.metrics[key] ?? -Infinity) ? item : best)
    : undefined;
  const items = [{ label: "Coverage", text: `${profile.career.games} games across ${profile.seasons.length} verified UPIKE seasons are represented.` }];
  if (peak) items.push({ label: "Peak Season", text: `${peak.label} is the highest recorded ${profile.primary_metric.label.toLowerCase()} season at ${formatMetric(peak.metrics[key])}.` });
  if (recorded.length > 1) {
    const previous = recorded[recorded.length - 2];
    const latest = recorded[recorded.length - 1];
    const priorValue = previous.metrics[key];
    const latestValue = latest.metrics[key];
    const change = priorValue ? ((latestValue - priorValue) / Math.abs(priorValue)) * 100 : 0;
    items.push({ label: "Trend", text: `${profile.primary_metric.label} ${change >= 0 ? "increased" : "decreased"} ${Math.abs(change).toFixed(1)}% from ${previous.label} to ${latest.label}.` });
  }
  const c = profile.career;
  if (key === "passing_yards" && c.pass_attempts) items.push({ label: "Efficiency", text: `${((c.completions / c.pass_attempts) * 100).toFixed(1)}% completions with a ${c.passing_touchdowns}:${c.pass_interceptions} touchdown-to-interception line.` });
  else if (key === "tackles" && c.games) items.push({ label: "Rate", text: `${(c.tackles / c.games).toFixed(1)} tackles per verified appearance, with ${formatMetric(c.tackles_for_loss)} tackles for loss.` });
  else if (key === "receiving_yards" && c.receptions) items.push({ label: "Efficiency", text: `${(c.receiving_yards / c.receptions).toFixed(1)} yards per reception across ${formatMetric(c.receptions)} catches.` });
  else if (key === "all_purpose_yards" && c.games) items.push({ label: "Rate", text: `${(c.all_purpose_yards / c.games).toFixed(1)} all-purpose yards per verified appearance.` });
  else if (key === "rushing_yards" && c.rushing_attempts) items.push({ label: "Efficiency", text: `${(c.rushing_yards / c.rushing_attempts).toFixed(1)} yards per carry across ${formatMetric(c.rushing_attempts)} attempts.` });
  return items;
}

function PlayerTrendChart({ profile }: { profile: PlayerProfile }) {
  const key = profile.primary_metric.key;
  const data = profile.seasons.map((item) => ({ season: item.label, total: item.metrics[key] ?? 0, perGame: item.games ? Number(((item.metrics[key] ?? 0) / item.games).toFixed(1)) : 0 }));
  return <div className="career-chart" aria-label={`${profile.primary_metric.label} by season`}><ResponsiveContainer width="100%" height="100%"><ComposedChart data={data} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}><CartesianGrid stroke="rgba(148,163,184,.12)" vertical={false} /><XAxis dataKey="season" stroke="#64748b" tick={{ fontSize: 10 }} /><YAxis yAxisId="left" stroke="#64748b" tick={{ fontSize: 10 }} /><YAxis yAxisId="right" orientation="right" stroke="#64748b" tick={{ fontSize: 10 }} /><Tooltip contentStyle={{ background: "#0b111c", border: "1px solid rgba(255,255,255,.12)", borderRadius: 8, fontSize: 11 }} /><Bar yAxisId="left" dataKey="total" name={profile.primary_metric.label} fill="#ff6a32" radius={[4, 4, 0, 0]} /><Line yAxisId="right" type="monotone" dataKey="perGame" name="Per Game" stroke="#5eead4" strokeWidth={2} dot={{ fill: "#5eead4", r: 3 }} /></ComposedChart></ResponsiveContainer></div>;
}

function ScheduleTable({ season }: { season: StatBoardSeason }) {
  return <DataPanel title="Schedule" subtitle={`${season.label} / ${season.schedule.length} games`}>
    <table className="stat-table min-w-[760px]"><thead><tr><th>Date</th><th>Opponent</th><th>Result</th><th>Status</th><th>Notes</th></tr></thead><tbody>{season.schedule.map((row) => <tr key={`${row.date}-${row.opponent}`} className={row.result.startsWith("W") ? "win-row" : row.result.startsWith("L") ? "loss-row" : ""}><td>{row.date}</td><td className="metric-name">{row.opponent}</td><td className="font-black">{row.result || "-"}</td><td>{row.status}</td><td className="text-slate-500">{row.notes || "-"}</td></tr>)}</tbody></table>
  </DataPanel>;
}

function DataPanel({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return <div className="overflow-hidden rounded-lg border border-white/10 bg-[#090e17]"><div className="flex items-center justify-between border-b border-white/10 px-4 py-3"><h2 className="text-sm font-black uppercase tracking-[.12em]">{title}</h2><span className="text-[10px] font-bold uppercase tracking-wider text-slate-600">{subtitle}</span></div><div className="overflow-x-auto">{children}</div></div>;
}

function RankValue({ value }: { value: string }) {
  const first = value === "1st";
  return <span className={cn("inline-flex min-w-9 justify-center rounded px-1.5 py-1 text-[10px] font-black", first ? "bg-orange text-[#080b10]" : "bg-white/[.06] text-slate-400")}>{value}</span>;
}

function RankChip({ label, value }: { label: string; value: string }) {
  return <div className="rounded-md border border-white/10 bg-white/[.03] px-4 py-2 text-right"><p className="text-[9px] font-bold uppercase tracking-[.18em] text-slate-600">{label} scoring</p><p className="text-xl font-black tabular-nums text-orange">{value}</p></div>;
}

function RecordCell({ label, value }: { label: string; value: string }) {
  return <div className="bg-[#090e17] px-4 py-3"><p className="text-[9px] font-bold uppercase tracking-[.16em] text-slate-600">{label}</p><p className="mt-1 text-xl font-black tabular-nums">{value}</p></div>;
}

function MetricCell({ label, value, negative }: { label: string; value: string; negative: boolean }) {
  return <div className={cn("rounded-md border px-4 py-4", negative ? "border-rose-400/10 bg-rose-400/[.035]" : "border-emerald-400/10 bg-emerald-400/[.035]")}><p className="text-[9px] font-bold uppercase tracking-[.13em] text-slate-600">{label}</p><p className={cn("mt-2 text-2xl font-black tabular-nums", negative ? "text-rose-300" : "text-emerald-300")}>{value}</p></div>;
}

function ViewButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
  return <button onClick={onClick} className={cn("whitespace-nowrap border-b-2 px-4 py-3 text-xs font-black uppercase tracking-[.1em]", active ? "border-orange text-white" : "border-transparent text-slate-600 hover:text-slate-300")}>{children}</button>;
}

function Count({ children }: { children: ReactNode }) {
  return <span className="ml-1 rounded bg-white/[.07] px-1.5 py-0.5 text-[9px] text-slate-500">{children}</span>;
}

function BoardLoading() { return <div className="grid min-h-screen place-items-center bg-[#05080e] text-xs font-bold uppercase tracking-[.2em] text-slate-600">Loading stats</div>; }
function BoardError() { return <div className="grid min-h-screen place-items-center bg-[#05080e] text-sm font-bold text-rose-300">Stat board unavailable</div>; }
