"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  api,
  type AnalyticsAggregate,
  type PlayAnalytics,
  type PlayAnalyticsPlayer,
  type PlayAnalyticsSnap,
} from "@/lib/api";
import { cn } from "@/lib/utils";

type AnalyticsView = "overview" | "calls" | "situations" | "games" | "players" | "snaps";
type Filters = { game_id?: string; player?: string; formation?: string; off_play?: string; situation?: string };

const VIEWS: Array<[AnalyticsView, string]> = [
  ["overview", "Overview"],
  ["calls", "Calls & Formations"],
  ["situations", "Situations"],
  ["games", "Games"],
  ["players", "Players"],
  ["snaps", "All Snaps"],
];

export function PlayAnalyticsPanel({ season = "2025", onPlayerSelect }: { season?: string; onPlayerSelect: (player: string) => void }) {
  const query = useQuery({ queryKey: ["play-analytics", season], queryFn: () => api.playAnalytics(season) });
  const [view, setView] = useState<AnalyticsView>("overview");
  const [filters, setFilters] = useState<Filters>({});
  const [selectedSnap, setSelectedSnap] = useState<PlayAnalyticsSnap | null>(null);
  const [selectedAnalyticsPlayer, setSelectedAnalyticsPlayer] = useState<PlayAnalyticsPlayer | null>(null);

  if (query.isLoading) return <AnalyticsLoading />;
  if (query.error || !query.data) return <AnalyticsError />;
  const data = query.data;

  function openPlayer(player: string) {
    if (season === "2024") {
      setSelectedAnalyticsPlayer(data.players.find((item) => item.player === player) ?? null);
    } else {
      onPlayerSelect(player);
    }
  }

  function drill(next: Filters) {
    setFilters(next);
    setView("snaps");
  }

  return <div className="space-y-4">
    <section className="grid grid-cols-2 gap-2 sm:grid-cols-4 xl:grid-cols-8">
      <AnalyticsMetric label="Tagged rows" value={data.coverage.tagged_rows} />
      <AnalyticsMetric label="Official links" value={`${data.coverage.linked_pct}%`} />
      <AnalyticsMetric label="Graded plays" value={data.overview.graded_plays} />
      <AnalyticsMetric label="Success" value={`${data.overview.success_rate}%`} tone="good" />
      <AnalyticsMetric label="Yards / play" value={data.overview.yards_per_graded_play} />
      <AnalyticsMetric label="Explosives" value={data.overview.explosives} tone="good" />
      <AnalyticsMetric label="Negative" value={data.overview.negative_plays} tone="bad" />
      <AnalyticsMetric label="Turnover events" value={data.overview.turnover_events} tone="bad" />
    </section>

    <div className="flex gap-1 overflow-x-auto rounded-lg border border-white/10 bg-[#090e17] p-1" role="tablist" aria-label="Play analytics views">
      {VIEWS.map(([key, label]) => <button key={key} role="tab" aria-selected={view === key} onClick={() => setView(key)} className={cn("whitespace-nowrap rounded-md px-3 py-2 text-[10px] font-black uppercase tracking-[.1em]", view === key ? "bg-orange text-[#070a0f]" : "text-slate-500 hover:bg-white/[.04] hover:text-white")}>{label}</button>)}
    </div>

    {view === "overview" && <Overview data={data} onDrill={drill} onSnap={setSelectedSnap} />}
    {view === "calls" && <Calls data={data} onDrill={drill} />}
    {view === "situations" && <Situations data={data} onDrill={drill} />}
    {view === "games" && <Games data={data} onDrill={drill} />}
    {view === "players" && <Players data={data} onDrill={drill} onPlayerSelect={openPlayer} />}
    {view === "snaps" && <Snaps data={data} filters={filters} setFilters={setFilters} onSnap={setSelectedSnap} />}

    <Definitions data={data} />
    {selectedSnap && <SnapDrawer snap={selectedSnap} onClose={() => setSelectedSnap(null)} onPlayer={(player) => { setSelectedSnap(null); openPlayer(player); }} />}
    {selectedAnalyticsPlayer && <AnalyticsPlayerDrawer player={selectedAnalyticsPlayer} onClose={() => setSelectedAnalyticsPlayer(null)} onDrill={(player) => { setSelectedAnalyticsPlayer(null); drill({ player }); }} />}
  </div>;
}

function Overview({ data, onDrill, onSnap }: { data: PlayAnalytics; onDrill: (filters: Filters) => void; onSnap: (snap: PlayAnalyticsSnap) => void }) {
  const gameChart = data.games.map((game) => ({
    gameId: game.game_id,
    name: compactOpponent(game.opponent),
    success: game.success_rate,
    ypp: game.yards_per_play,
    margin: game.point_margin,
    pointsLost: Math.max(0, -(game.point_margin ?? 0)),
  }));
  return <div className="grid gap-4 xl:grid-cols-[1.35fr_.65fr]">
    <section className="analytics-panel">
      <PanelHeader title="Game Efficiency" meta="Success rate + yards per tagged play" />
      <div className="h-[330px] p-3">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={gameChart} margin={{ top: 14, right: 28, left: -18, bottom: 34 }}>
            <CartesianGrid stroke="rgba(148,163,184,.12)" vertical={false} />
            <XAxis dataKey="name" angle={-28} textAnchor="end" interval={0} stroke="#64748b" tick={{ fontSize: 9 }} />
            <YAxis yAxisId="left" stroke="#64748b" tick={{ fontSize: 9 }} domain={[0, 80]} />
            <YAxis yAxisId="right" orientation="right" stroke="#64748b" tick={{ fontSize: 9 }} />
            <Tooltip contentStyle={tooltipStyle} />
            <Line yAxisId="left" dataKey="success" name="Success %" stroke="#ff6a32" strokeWidth={3} dot={{ r: 3, fill: "#ff6a32" }} />
            <Line yAxisId="right" dataKey="ypp" name="Yards / play" stroke="#5eead4" strokeWidth={2} dot={{ r: 3, fill: "#5eead4" }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
    <section className="analytics-panel">
      <PanelHeader title="Coach Review Queue" meta="Calculated / minimum samples enforced" />
      <div className="divide-y divide-white/10">
        {data.recommendations.map((item) => <button key={item.title} onClick={() => onDrill(item.filter)} className="block w-full px-4 py-4 text-left hover:bg-white/[.035]">
          <span className={cn("rounded px-1.5 py-1 text-[8px] font-black uppercase tracking-widest", item.type === "review" || item.type === "game" ? "bg-rose-400/10 text-rose-300" : "bg-emerald-400/10 text-emerald-300")}>{item.type}</span>
          <strong className="mt-2 block text-sm">{item.title}</strong>
          <p className="mt-1 text-xs leading-5 text-slate-500">{item.evidence}</p>
        </button>)}
      </div>
    </section>
    <section className="analytics-panel xl:col-span-2">
      <PanelHeader title="Where Scoreboard Points Were Lost" meta="Actual final deficit in losses / zero for wins" />
      <div className="h-[260px] p-3">
        <ResponsiveContainer width="100%" height="100%"><BarChart data={gameChart} margin={{ top: 12, right: 12, left: -20, bottom: 34 }}><CartesianGrid stroke="rgba(148,163,184,.12)" vertical={false} /><XAxis dataKey="name" angle={-24} textAnchor="end" interval={0} stroke="#64748b" tick={{ fontSize: 9 }} /><YAxis stroke="#64748b" tick={{ fontSize: 9 }} /><Tooltip contentStyle={tooltipStyle} /><Bar dataKey="pointsLost" name="Final deficit" radius={[4, 4, 0, 0]} onClick={(_, index) => { const game = gameChart[index]; if (game) onDrill({ game_id: game.gameId }); }}>{gameChart.map((game) => <Cell key={game.gameId} fill={game.pointsLost > 0 ? "#fb7185" : "#334155"} />)}</Bar></BarChart></ResponsiveContainer>
      </div>
    </section>
    <section className="analytics-panel xl:col-span-2">
      <PanelHeader title="Field Position Map" meta="All graded snaps / click a marker" />
      <FootballField snaps={data.snaps.filter((snap) => snap.success !== null)} onSnap={onSnap} />
    </section>
  </div>;
}

function Calls({ data, onDrill }: { data: PlayAnalytics; onDrill: (filters: Filters) => void }) {
  return <div className="space-y-4">
    <div className="grid gap-4 lg:grid-cols-2">
      <AggregatePanel title="Top Qualified Calls" meta="8+ graded snaps" rows={data.top_calls} onRow={(label) => onDrill({ off_play: label })} />
      <AggregatePanel title="Calls To Review" meta="Lowest qualified success rate" rows={data.review_calls} onRow={(label) => onDrill({ off_play: label })} review />
    </div>
    <div className="grid gap-4 xl:grid-cols-2">
      <AggregateTable title="All Play Calls" rows={data.play_calls} onRow={(label) => onDrill({ off_play: label })} />
      <AggregateTable title="All Formations" rows={data.formations} onRow={(label) => onDrill({ formation: label })} />
    </div>
  </div>;
}

function Situations({ data, onDrill }: { data: PlayAnalytics; onDrill: (filters: Filters) => void }) {
  return <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
    {Object.entries(data.situations).map(([key, rows]) => <section key={key} className="analytics-panel">
      <PanelHeader title={key.replaceAll("_", " ")} meta={`${rows.length} groups`} />
      <div className="h-56 p-3">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} layout="vertical" margin={{ left: 28, right: 18 }}>
            <CartesianGrid stroke="rgba(148,163,184,.10)" horizontal={false} />
            <XAxis type="number" domain={[0, 100]} stroke="#64748b" tick={{ fontSize: 9 }} />
            <YAxis type="category" dataKey="label" width={95} stroke="#64748b" tick={{ fontSize: 9 }} />
            <Tooltip contentStyle={tooltipStyle} />
            <Bar dataKey="success_rate" name="Success %" radius={[0, 4, 4, 0]} onClick={(_, index) => { const row = rows[index]; if (row) onDrill({ situation: row.label }); }}>
              {rows.map((row) => <Cell key={row.label} fill={(row.success_rate ?? 0) >= 50 ? "#34d399" : (row.success_rate ?? 0) >= 40 ? "#ff6a32" : "#fb7185"} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="border-t border-white/10 px-4 py-3 text-[10px] text-slate-500">Bars are clickable. Sample sizes are shown in tooltips.</div>
    </section>)}
  </div>;
}

function Games({ data, onDrill }: { data: PlayAnalytics; onDrill: (filters: Filters) => void }) {
  return <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
    {data.games.map((game) => <button key={game.game_id} onClick={() => onDrill({ game_id: game.game_id })} className="analytics-panel p-4 text-left transition hover:border-orange/40 hover:bg-orange/[.025]">
      <div className="flex items-start justify-between gap-3"><div><span className="text-[9px] font-black uppercase tracking-widest text-slate-600">{game.date}</span><h3 className="mt-1 text-lg font-black">{game.opponent}</h3></div><span className={cn("rounded px-2 py-1 text-sm font-black", game.result.startsWith("W") ? "bg-emerald-400/10 text-emerald-300" : "bg-rose-400/10 text-rose-300")}>{game.result}</span></div>
      <div className="mt-4 grid grid-cols-4 gap-px overflow-hidden rounded bg-white/10">
        <MiniMetric label="Success" value={`${game.success_rate ?? "-"}%`} />
        <MiniMetric label="Y/Play" value={game.yards_per_play ?? "-"} />
        <MiniMetric label="Explosive" value={game.explosives} />
        <MiniMetric label="Negative" value={game.negative_plays} bad />
      </div>
      <div className="mt-3 flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-slate-600"><span>{game.linked_rows}/{game.tagged_rows} linked</span><span>Actual margin {signed(game.point_margin)}</span></div>
      <div className="mt-3 grid grid-cols-3 gap-2 text-xs"><GameOfficial label="Official yards" value={game.official_team_stats.yds} /><GameOfficial label="Pass" value={game.official_team_stats.pass} /><GameOfficial label="Rush" value={game.official_team_stats.rush} /></div>
    </button>)}
  </div>;
}

function Players({ data, onDrill, onPlayerSelect }: { data: PlayAnalytics; onDrill: (filters: Filters) => void; onPlayerSelect: (player: string) => void }) {
  return <section className="analytics-panel overflow-hidden">
    <PanelHeader title="Player Attribution" meta={`${data.players.filter((player) => player.plays > 0).length} players linked to tagged snaps / ${data.players.length} official profiles`} />
    <div className="overflow-x-auto">
      <table className="stat-table min-w-[1200px]"><thead><tr><th>Player</th><th>Games</th><th>Linked plays</th><th>Passing</th><th>Pass yds</th><th>Pass TD</th><th>Rush</th><th>Rush yds</th><th>Rush TD</th><th>Targets</th><th>Rec</th><th>Rec yds</th><th>Rec TD</th><th>Explosive</th></tr></thead><tbody>
        {data.players.map((player) => <tr key={player.player}><td className="metric-name"><div className="flex min-w-[180px] items-center justify-between gap-2"><button className="player-link" onClick={() => onPlayerSelect(player.player)}>{player.player}<span>›</span></button><button disabled={!player.plays} onClick={() => onDrill({ player: player.player })} className="rounded border border-white/10 px-2 py-1 text-[8px] font-black uppercase tracking-wider text-slate-500 enabled:hover:border-orange/40 enabled:hover:text-orange disabled:opacity-25">Snaps</button></div></td><td>{player.games}</td><td>{player.plays}</td><td>{player.completions}-{player.pass_attempts}</td><td>{player.passing_yards}</td><td>{player.passing_touchdowns}</td><td>{player.rush_attempts}</td><td>{player.rushing_yards}</td><td>{player.rushing_touchdowns}</td><td>{player.targets}</td><td>{player.receptions}</td><td>{player.receiving_yards}</td><td>{player.receiving_touchdowns}</td><td>{player.explosives}</td></tr>)}
      </tbody></table>
    </div>
  </section>;
}

function Snaps({ data, filters, setFilters, onSnap }: { data: PlayAnalytics; filters: Filters; setFilters: (filters: Filters) => void; onSnap: (snap: PlayAnalyticsSnap) => void }) {
  const filtered = useMemo(() => data.snaps.filter((snap) => {
    if (filters.game_id && snap.game_id !== filters.game_id) return false;
    if (filters.player && !snap.players.includes(filters.player)) return false;
    if (filters.formation && snap.formation !== filters.formation) return false;
    if (filters.off_play && String(snap.off_play) !== filters.off_play) return false;
    if (filters.situation && ![String(snap.down), snap.distance_bucket, snap.field_zone, snap.play_type, snap.motion ? "Motion" : "No motion tag", snap.shift ? "Shift" : "No shift tag"].includes(filters.situation)) return false;
    return true;
  }), [data.snaps, filters]);
  const shown = filtered.slice(0, 250);
  return <div className="space-y-4">
    <section className="analytics-panel p-3">
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
        <FilterSelect value={filters.game_id} label="All games" options={data.games.map((item) => [item.game_id, item.opponent])} onChange={(value) => setFilters({ ...filters, game_id: value })} />
        <FilterSelect value={filters.player} label="All players" options={data.players.filter((item) => item.plays > 0).map((item) => [item.player, item.player])} onChange={(value) => setFilters({ ...filters, player: value })} />
        <FilterSelect value={filters.formation} label="All formations" options={data.formations.map((item) => [item.label, item.label])} onChange={(value) => setFilters({ ...filters, formation: value })} />
        <FilterSelect value={filters.off_play} label="All calls" options={data.play_calls.map((item) => [item.label, item.label])} onChange={(value) => setFilters({ ...filters, off_play: value })} />
        <button onClick={() => setFilters({})} className="rounded-md border border-white/10 px-3 py-2 text-[10px] font-black uppercase tracking-wider text-slate-500 hover:border-orange/40 hover:text-orange">Clear filters</button>
      </div>
      <p className="mt-3 text-[10px] font-bold uppercase tracking-wider text-slate-600">{filtered.length} snaps matched / showing {shown.length}{filtered.length > shown.length ? " — narrow filters to see more" : ""}</p>
    </section>
    <section className="analytics-panel">
      <PanelHeader title="Filtered Field Map" meta={`${filtered.length} coaching rows`} />
      <FootballField snaps={filtered.filter((snap) => snap.yard_line !== null)} onSnap={onSnap} />
    </section>
    <section className="analytics-panel overflow-hidden">
      <PanelHeader title="Snap Ledger" meta="Click any row for full source + tags" />
      <div className="max-h-[720px] overflow-auto"><table className="stat-table min-w-[1500px]"><thead className="sticky top-0 z-10 bg-[#090e17]"><tr><th>Snap</th><th>Game</th><th>Q</th><th>Down</th><th>Spot</th><th>Gain</th><th>Result</th><th>Formation</th><th>Call</th><th>Motion</th><th>Players</th><th>Success</th><th>Link</th></tr></thead><tbody>
        {shown.map((snap) => <tr key={snap.id} onClick={() => onSnap(snap)} className="cursor-pointer hover:bg-orange/[.035]"><td className="font-black text-orange">#{snap.game_snap}</td><td className="metric-name">{compactOpponent(snap.opponent)}</td><td>{snap.quarter ?? "-"}</td><td>{snap.down ? `${snap.down}&${snap.distance ?? "?"}` : "-"}</td><td>{spotLabel(snap.yard_line)}</td><td className={cn("font-black", (snap.gain ?? 0) < 0 ? "text-rose-300" : "")}>{snap.gain ?? "-"}</td><td>{snap.result}</td><td>{snap.formation ?? "-"}</td><td>{snap.off_play ?? "-"}</td><td>{snap.motion ?? "-"}</td><td className="max-w-[240px] truncate">{snap.players.join(", ") || "-"}</td><td><StatusPill snap={snap} /></td><td><Confidence value={snap.match_confidence} /></td></tr>)}
      </tbody></table></div>
    </section>
  </div>;
}

function FootballField({ snaps, onSnap }: { snaps: PlayAnalyticsSnap[]; onSnap: (snap: PlayAnalyticsSnap) => void }) {
  const markers = snaps.length > 180 ? snaps.filter((_, index) => index % Math.ceil(snaps.length / 180) === 0) : snaps;
  return <div className="p-4"><div className="football-field" aria-label={`Football field showing ${markers.length} snap positions`}>
    <div className="end-zone left">UPIKE</div><div className="end-zone right">OPP</div>
    {[10,20,30,40,50,60,70,80,90].map((line) => <div key={line} className="yard-line" style={{ left: `${line}%` }}><span>{line <= 50 ? line : 100-line}</span></div>)}
    {markers.map((snap, index) => <button key={snap.id} onClick={() => onSnap(snap)} title={`${snap.opponent}: ${snap.description ?? snap.result}`} className={cn("field-marker", snap.turnover_event ? "turnover" : snap.touchdown ? "touchdown" : snap.explosive ? "explosive" : snap.success ? "success" : snap.success === false ? "failed" : "ungraded")} style={{ left: `${fieldPercent(snap.yard_line)}%`, top: `${16 + (index % 7) * 10}%` }} aria-label={`Open ${snap.id}`} />)}
  </div><div className="mt-3 flex flex-wrap gap-3 text-[9px] font-bold uppercase tracking-wider text-slate-600"><Legend tone="success" label="Successful" /><Legend tone="failed" label="Failed" /><Legend tone="explosive" label="Explosive" /><Legend tone="turnover" label="Turnover event" /><span>{markers.length}/{snaps.length} markers plotted</span></div></div>;
}

function SnapDrawer({ snap, onClose, onPlayer }: { snap: PlayAnalyticsSnap; onClose: () => void; onPlayer: (player: string) => void }) {
  return <div className="player-drawer-layer" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><aside className="player-drawer" role="dialog" aria-modal="true" aria-label={`Snap ${snap.game_snap}`}>
    <header className="player-drawer-header"><div><p className="text-[10px] font-black uppercase tracking-[.18em] text-orange">{snap.date} / {snap.opponent}</p><h2 className="mt-1 text-3xl font-black">Snap #{snap.game_snap}</h2></div><button onClick={onClose} className="player-drawer-close" aria-label="Close snap">×</button></header>
    <div className="player-drawer-body space-y-6">
      <section><div className="drawer-section-title"><h3>Official Play</h3><span><Confidence value={snap.match_confidence} /></span></div><p className="mt-3 rounded-lg border border-white/10 bg-white/[.025] p-4 text-sm leading-6 text-slate-200">{snap.description ?? "No official description was aligned to this coaching row."}</p><a href={snap.source_url} target="_blank" rel="noreferrer" className="history-source-link mt-2 inline-flex">Official gamebook play-by-play ↗</a></section>
      <section><div className="drawer-section-title"><h3>Situation</h3><span>{snap.context ?? "Coaching tags only"}</span></div><div className="career-total-grid mt-3"><DrawerMetric label="Quarter" value={snap.quarter ?? "-"} /><DrawerMetric label="Down" value={snap.down ?? "-"} /><DrawerMetric label="Distance" value={snap.distance ?? "-"} /><DrawerMetric label="Spot" value={spotLabel(snap.yard_line)} /><DrawerMetric label="Gain" value={snap.gain ?? "-"} /><DrawerMetric label="Result" value={snap.result} /></div></section>
      <section><div className="drawer-section-title"><h3>Coaching Tags</h3><span>Excel row {snap.season_snap}</span></div><div className="drawer-stat-grid mt-3"><DrawerMetric label="Formation" value={snap.formation ?? "-"} /><DrawerMetric label="Play Call" value={snap.off_play ?? "-"} /><DrawerMetric label="Shift" value={snap.shift ?? "-"} /><DrawerMetric label="Motion" value={snap.motion ?? "-"} /><DrawerMetric label="Front" value={snap.def_front ?? "-"} /><DrawerMetric label="Blitz" value={snap.blitz ?? "-"} /><DrawerMetric label="Coverage" value={snap.coverage ?? "-"} /><DrawerMetric label="Field Zone" value={snap.field_zone} /></div></section>
      <section><div className="drawer-section-title"><h3>Players</h3><span>{snap.players.length} attributed</span></div><div className="mt-3 flex flex-wrap gap-2">{snap.players.length ? snap.players.map((player) => <button key={player} onClick={() => onPlayer(player)} className="rounded-md border border-white/10 bg-white/[.03] px-3 py-2 text-xs font-bold hover:border-orange/40 hover:text-orange">{player}</button>) : <span className="text-xs text-slate-600">No player identity linked.</span>}</div></section>
    </div>
  </aside></div>;
}

function AnalyticsPlayerDrawer({ player, onClose, onDrill }: { player: PlayAnalyticsPlayer; onClose: () => void; onDrill: (player: string) => void }) {
  const chart = player.by_game.map((game) => ({
    ...game,
    opponent: compactOpponent(game.opponent),
    totalYards: game.passing_yards + game.rushing_yards + game.receiving_yards,
  }));
  return <div className="player-drawer-layer" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><aside className="player-drawer" role="dialog" aria-modal="true" aria-label={`${player.player} 2024-25 play analytics`}>
    <header className="player-drawer-header"><div><p className="text-[10px] font-black uppercase tracking-[.18em] text-orange">2024-25 / HUDL + official gamebooks</p><h2 className="mt-1 text-3xl font-black">{player.player}</h2></div><button onClick={onClose} className="player-drawer-close" aria-label="Close player analytics">×</button></header>
    <div className="player-drawer-body space-y-7">
      <section><div className="drawer-section-title"><h3>Official Gamebook Totals</h3><span>{player.games} games / {player.plays} HUDL-linked snaps</span></div><div className="career-total-grid mt-3"><DrawerMetric label="Passing Yards" value={player.passing_yards} /><DrawerMetric label="Pass TD" value={player.passing_touchdowns} /><DrawerMetric label="Rushing Yards" value={player.rushing_yards} /><DrawerMetric label="Rush TD" value={player.rushing_touchdowns} /><DrawerMetric label="Receiving Yards" value={player.receiving_yards} /><DrawerMetric label="Rec TD" value={player.receiving_touchdowns} /><DrawerMetric label="HUDL Explosives" value={player.explosives} /><DrawerMetric label="HUDL Successful" value={player.successful_plays} /></div></section>
      <section><div className="drawer-section-title"><h3>Game Trend</h3><span>Official per-game player tables</span></div><div className="mt-3 h-64"><ResponsiveContainer width="100%" height="100%"><LineChart data={chart} margin={{ top: 12, right: 16, left: -18, bottom: 42 }}><CartesianGrid stroke="rgba(148,163,184,.12)" vertical={false} /><XAxis dataKey="opponent" angle={-28} textAnchor="end" interval={0} stroke="#64748b" tick={{ fontSize: 9 }} /><YAxis stroke="#64748b" tick={{ fontSize: 9 }} /><Tooltip contentStyle={tooltipStyle} /><Line dataKey="totalYards" name="Official yards" stroke="#ff6a32" strokeWidth={3} dot={{ r: 3 }} /></LineChart></ResponsiveContainer></div></section>
      <section><div className="drawer-section-title"><h3>Game Splits</h3><span>{chart.length} linked games</span></div><div className="mt-3 overflow-hidden rounded-lg border border-white/10">{chart.map((game) => <div key={game.game_id} className="grid grid-cols-[60px_1fr_repeat(4,54px)] items-center gap-2 border-b border-white/10 px-3 py-2 text-xs last:border-0"><span className="text-slate-600">{game.date}</span><strong>{game.opponent}</strong><span title="Passing yards">P {game.passing_yards}</span><span title="Rushing yards">R {game.rushing_yards}</span><span title="Receiving yards">C {game.receiving_yards}</span><span title="Touchdowns">TD {game.touchdowns}</span></div>)}</div></section>
      <button onClick={() => onDrill(player.player)} className="w-full rounded-md bg-orange px-4 py-3 text-xs font-black uppercase tracking-wider text-[#070a0f]">Open all linked snaps</button>
      <p className="text-[10px] leading-5 text-slate-600">Passing, rushing, receiving, touchdowns, and the game trend are summed from the individual tables in all supplied official gamebooks. Explosives, successful plays, and linked snaps come from the HUDL-to-play-by-play alignment.</p>
    </div>
  </aside></div>;
}

function AggregatePanel({ title, meta, rows, onRow, review }: { title: string; meta: string; rows: AnalyticsAggregate[]; onRow: (label: string) => void; review?: boolean }) {
  return <section className="analytics-panel"><PanelHeader title={title} meta={meta} /><div className="divide-y divide-white/10">{rows.slice(0, 8).map((row, index) => <button key={row.label} onClick={() => onRow(row.label)} className="grid w-full grid-cols-[28px_1fr_auto_auto] items-center gap-3 px-4 py-3 text-left hover:bg-white/[.035]"><span className={cn("grid h-7 w-7 place-items-center rounded text-xs font-black", review ? "bg-rose-400/10 text-rose-300" : "bg-emerald-400/10 text-emerald-300")}>{index + 1}</span><span><strong className="block text-sm">{row.label}</strong><small className="text-[10px] text-slate-600">{row.graded_plays} graded / {row.plays} rows</small></span><span className="text-right"><strong className="block tabular-nums">{row.success_rate ?? "-"}%</strong><small className="text-[9px] uppercase text-slate-600">success</small></span><span className="text-right"><strong className="block tabular-nums">{row.yards_per_play ?? "-"}</strong><small className="text-[9px] uppercase text-slate-600">Y/play</small></span></button>)}</div></section>;
}

function AggregateTable({ title, rows, onRow }: { title: string; rows: AnalyticsAggregate[]; onRow: (label: string) => void }) {
  return <section className="analytics-panel overflow-hidden"><PanelHeader title={title} meta={`${rows.length} tagged groups`} /><div className="max-h-[620px] overflow-auto"><table className="stat-table min-w-[720px]"><thead className="sticky top-0 bg-[#090e17]"><tr><th>Name</th><th>Rows</th><th>Graded</th><th>Success</th><th>Y/Play</th><th>Explosive</th><th>TD</th><th>Negative</th></tr></thead><tbody>{rows.map((row) => <tr key={row.label} onClick={() => onRow(row.label)} className="cursor-pointer"><td className="metric-name">{row.label}</td><td>{row.plays}</td><td>{row.graded_plays}</td><td>{row.success_rate ?? "-"}%</td><td>{row.yards_per_play ?? "-"}</td><td>{row.explosives}</td><td>{row.touchdowns}</td><td>{row.negative_plays}</td></tr>)}</tbody></table></div></section>;
}

function Definitions({ data }: { data: PlayAnalytics }) { return <details className="analytics-panel"><summary className="cursor-pointer list-none px-4 py-3 text-[10px] font-black uppercase tracking-[.13em] text-slate-500">Method, thresholds & data quality</summary><div className="grid gap-3 border-t border-white/10 p-4 md:grid-cols-2">{Object.entries(data.definitions).map(([key, value]) => <div key={key}><strong className="text-[9px] uppercase tracking-wider text-orange">{key.replaceAll("_", " ")}</strong><p className="mt-1 text-xs leading-5 text-slate-500">{value}</p></div>)}</div></details>; }
function PanelHeader({ title, meta }: { title: string; meta: string }) { return <header className="flex items-center justify-between gap-3 border-b border-white/10 px-4 py-3"><h2 className="text-xs font-black uppercase tracking-[.12em]">{title}</h2><span className="text-right text-[9px] font-bold uppercase tracking-wider text-slate-600">{meta}</span></header>; }
function AnalyticsMetric({ label, value, tone }: { label: string; value: string | number; tone?: "good" | "bad" }) { return <div className="rounded-lg border border-white/10 bg-[#090e17] p-3"><span className="text-[8px] font-black uppercase tracking-[.14em] text-slate-600">{label}</span><strong className={cn("mt-1 block text-2xl tabular-nums", tone === "good" ? "text-emerald-300" : tone === "bad" ? "text-rose-300" : "text-white")}>{value}</strong></div>; }
function MiniMetric({ label, value, bad }: { label: string; value: string | number; bad?: boolean }) { return <div className="bg-[#080d15] p-2"><span className="block text-[7px] font-black uppercase tracking-wider text-slate-600">{label}</span><strong className={cn("mt-1 block tabular-nums", bad && "text-rose-300")}>{value}</strong></div>; }
function GameOfficial({ label, value }: { label: string; value: string | null | undefined }) { return <div><span className="block text-[8px] font-bold uppercase text-slate-600">{label}</span><strong>{value ?? "-"}</strong></div>; }
function DrawerMetric({ label, value }: { label: string; value: string | number }) { return <div><span>{label}</span><strong>{value}</strong></div>; }
function FilterSelect({ value, label, options, onChange }: { value?: string; label: string; options: string[][]; onChange: (value?: string) => void }) { return <select value={value ?? ""} onChange={(event) => onChange(event.target.value || undefined)} className="rounded-md border border-white/10 bg-[#070b12] px-3 py-2 text-xs font-bold text-slate-300 outline-none focus:border-orange"><option value="">{label}</option>{options.map(([key, text]) => <option key={key} value={key}>{text}</option>)}</select>; }
function StatusPill({ snap }: { snap: PlayAnalyticsSnap }) { const label = snap.touchdown ? "TD" : snap.turnover_event ? "TO" : snap.explosive ? "EXP" : snap.success === true ? "YES" : snap.success === false ? "NO" : "-"; return <span className={cn("rounded px-1.5 py-1 text-[8px] font-black", snap.turnover_event || snap.success === false ? "bg-rose-400/10 text-rose-300" : snap.touchdown || snap.explosive || snap.success ? "bg-emerald-400/10 text-emerald-300" : "bg-white/[.05] text-slate-600")}>{label}</span>; }
function Confidence({ value }: { value: PlayAnalyticsSnap["match_confidence"] }) { return <span className={cn("rounded px-1.5 py-1 text-[8px] font-black uppercase", value === "high" ? "bg-emerald-400/10 text-emerald-300" : value === "medium" ? "bg-amber-400/10 text-amber-300" : "bg-rose-400/10 text-rose-300")}>{value}</span>; }
function Legend({ tone, label }: { tone: string; label: string }) { return <span className="inline-flex items-center gap-1.5"><i className={`legend-dot ${tone}`} />{label}</span>; }
function fieldPercent(value: number | null): number { if (value === null) return 50; return Math.max(4, Math.min(96, value <= 0 ? Math.abs(value) : 100 - value)); }
function spotLabel(value: number | null): string { if (value === null) return "-"; if (Math.abs(value) === 50) return "50"; return value < 0 ? `OWN ${Math.abs(value)}` : `OPP ${value}`; }
function compactOpponent(value: string): string { return value.replace(/^at /, "").replace(/\s*\([^)]*\)/g, "").trim(); }
function signed(value: number | null): string { if (value === null) return "-"; return value > 0 ? `+${value}` : String(value); }
function AnalyticsLoading() { return <div className="analytics-panel grid min-h-[420px] place-items-center text-xs font-black uppercase tracking-widest text-slate-600">Building play board</div>; }
function AnalyticsError() { return <div className="analytics-panel grid min-h-[420px] place-items-center p-6 text-center text-sm text-rose-300">Play analytics could not be loaded.</div>; }
const tooltipStyle = { background: "#0b111c", border: "1px solid rgba(255,255,255,.12)", borderRadius: 8, fontSize: 11 };
