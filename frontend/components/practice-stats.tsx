"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  api,
  type Practice,
  type PracticeInput,
  type PracticePlay,
  type PracticePlayInput,
  type PracticeSummary,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const tooltipStyle = {
  background: "#0b111c",
  border: "1px solid rgba(255,255,255,.12)",
  borderRadius: 8,
  fontSize: 11,
};

const emptyPlay: PracticePlayInput = {
  sequence: 1,
  quarterback_number: "",
  quarterback_name: "",
  intended_receiver: "",
  result: "INCOMPLETE",
  notes: "",
};

export function PracticeStatsPanel({ season = 2026 }: { season?: number }) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["practice-dashboard", season],
    queryFn: () => api.practiceDashboard(season),
  });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const dashboard = query.data;
  const practices = dashboard?.practices ?? [];
  const selected = practices.find((item) => item.id === selectedId) ?? practices[0];

  useEffect(() => {
    if (practices.length && !practices.some((item) => item.id === selectedId)) {
      setSelectedId(practices[0].id);
    }
  }, [practices, selectedId]);

  async function mutate(action: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await action();
      await queryClient.invalidateQueries({ queryKey: ["practice-dashboard", season] });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save practice data");
      throw caught;
    } finally {
      setBusy(false);
    }
  }

  if (query.isLoading) {
    return <div className="analytics-panel p-8 text-center text-xs font-black uppercase tracking-[.15em] text-slate-600">Loading practice statistics</div>;
  }
  if (query.error || !dashboard) {
    return <div className="analytics-panel p-8 text-center text-sm font-bold text-rose-300">Practice database unavailable</div>;
  }

  const trend = [...practices].reverse().map((practice) => ({
    label: practice.practice_date ?? practice.title,
    completion: practice.summary.completion_pct ?? 0,
    attempts: practice.summary.attempts,
  }));

  return <div className="space-y-4">
    <section className="flex flex-col gap-3 rounded-lg border border-white/10 bg-[#090e17] p-4 md:flex-row md:items-center md:justify-between">
      <div><h2 className="text-sm font-black uppercase tracking-[.12em]">Practice Statistics</h2><p className="mt-1 text-[10px] font-bold uppercase tracking-wider text-slate-600">2026-27 / {practices.length} practices / {dashboard.overview.plays} graded rows</p></div>
      <button onClick={() => setCreating((value) => !value)} className="rounded-md bg-orange px-4 py-2 text-[10px] font-black uppercase tracking-[.1em] text-[#070a0f]">{creating ? "Cancel" : "New Practice"}</button>
    </section>

    {creating ? <NewPracticeForm season={season} busy={busy} onCreate={async (payload) => {
      let createdId = "";
      await mutate(async () => { const created = await api.createPractice(payload); createdId = created.id; });
      setSelectedId(createdId);
      setCreating(false);
    }} /> : null}

    {error ? <div className="rounded-md border border-rose-400/20 bg-rose-400/[.06] px-4 py-3 text-xs text-rose-300">{error}</div> : null}

    <SummaryCards summary={dashboard.overview} practiceCount={practices.length} quarterbackCount={dashboard.quarterbacks.length} />

    <section className="grid gap-4 xl:grid-cols-2">
      <ChartPanel title="Completion Trend" meta={`${trend.length} practices`}>
        {trend.length ? <ResponsiveContainer width="100%" height="100%"><LineChart data={trend} margin={{ top: 10, right: 14, left: -18, bottom: 34 }}><CartesianGrid stroke="rgba(148,163,184,.12)" vertical={false} /><XAxis dataKey="label" angle={-18} textAnchor="end" interval={0} stroke="#64748b" tick={{ fontSize: 9 }} /><YAxis domain={[0, 100]} stroke="#64748b" tick={{ fontSize: 9 }} unit="%" /><Tooltip contentStyle={tooltipStyle} /><Line type="monotone" dataKey="completion" name="Completion %" stroke="#ff6a32" strokeWidth={3} dot={{ fill: "#ff6a32", r: 3 }} /></LineChart></ResponsiveContainer> : <EmptyChart />}
      </ChartPanel>
      <ChartPanel title="QB Attempts" meta={`${dashboard.quarterbacks.length} quarterbacks`}>
        {dashboard.quarterbacks.length ? <ResponsiveContainer width="100%" height="100%"><BarChart data={dashboard.quarterbacks} margin={{ top: 10, right: 14, left: -18, bottom: 34 }}><CartesianGrid stroke="rgba(148,163,184,.12)" vertical={false} /><XAxis dataKey="display_name" angle={-18} textAnchor="end" interval={0} stroke="#64748b" tick={{ fontSize: 9 }} /><YAxis stroke="#64748b" tick={{ fontSize: 9 }} /><Tooltip contentStyle={tooltipStyle} /><Bar dataKey="completions" name="Complete" stackId="attempts" fill="#34d399" /><Bar dataKey="incompletions" name="Incomplete" stackId="attempts" fill="#fb7185" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer> : <EmptyChart />}
      </ChartPanel>
    </section>

    <QuarterbackTable rows={dashboard.quarterbacks} />

    <section className="analytics-panel">
      <div className="border-b border-white/10 p-3"><div className="flex gap-2 overflow-x-auto">
        {practices.map((practice) => <button key={practice.id} onClick={() => setSelectedId(practice.id)} className={cn("min-w-[170px] rounded-md border px-3 py-2 text-left", selected?.id === practice.id ? "border-orange bg-orange/10" : "border-white/10 bg-white/[.02] hover:border-white/25")}><strong className="block truncate text-xs">{practice.title}</strong><span className="mt-1 block text-[9px] font-bold uppercase tracking-wider text-slate-600">{practice.practice_date ?? "Date not set"} / {practice.summary.attempts} attempts</span></button>)}
        {!practices.length ? <span className="px-2 py-3 text-xs text-slate-600">Create the first practice to begin tracking.</span> : null}
      </div></div>
      {selected ? <PracticeEditor key={selected.id} practice={selected} busy={busy} onUpdate={(payload) => mutate(() => api.updatePractice(selected.id, payload))} onDelete={async () => {
        if (!window.confirm(`Delete ${selected.title} and all of its plays?`)) return;
        await mutate(() => api.deletePractice(selected.id));
        setSelectedId(null);
      }} onCreatePlay={(payload) => mutate(() => api.createPracticePlay(selected.id, payload))} onUpdatePlay={(id, payload) => mutate(() => api.updatePracticePlay(id, payload))} onDeletePlay={async (id) => {
        if (!window.confirm("Delete this practice play?")) return;
        await mutate(() => api.deletePracticePlay(id));
      }} /> : null}
    </section>
  </div>;
}

function SummaryCards({ summary, practiceCount, quarterbackCount }: { summary: PracticeSummary; practiceCount: number; quarterbackCount: number }) {
  const cards = [
    ["Practices", practiceCount], ["Quarterbacks", quarterbackCount], ["Attempts", summary.attempts],
    ["Completions", summary.completions], ["Completion", summary.completion_pct === null ? "-" : `${summary.completion_pct}%`],
    ["On Target", summary.on_target], ["Positive Reads", summary.positive_reads], ["Negative Reads", summary.negative_reads],
    ["Positive Timing", summary.positive_timing], ["Receiver Drops", summary.receiver_drops],
  ];
  return <section className="grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-white/10 bg-white/10 sm:grid-cols-5">{cards.map(([label, value]) => <div key={label} className="bg-[#090e17] px-4 py-4"><p className="text-[9px] font-bold uppercase tracking-[.13em] text-slate-600">{label}</p><p className="mt-2 text-2xl font-black tabular-nums">{value}</p></div>)}</section>;
}

function QuarterbackTable({ rows }: { rows: Array<PracticeSummary & { key: string; display_name: string; quarterback_number: string | null; practices: number }> }) {
  return <section className="analytics-panel"><div className="flex items-center justify-between border-b border-white/10 px-4 py-3"><h3 className="text-sm font-black uppercase tracking-[.12em]">Quarterback Summary</h3><span className="text-[10px] font-bold uppercase tracking-wider text-slate-600">Coach-entered practice data</span></div><div className="overflow-x-auto"><table className="stat-table min-w-[1050px]"><thead><tr><th>#</th><th>Quarterback</th><th>Practices</th><th>C-A</th><th>Comp%</th><th>On Target</th><th>Positive Read</th><th>Negative Read</th><th>Positive Timing</th><th>Poor Timing</th><th>Drops</th><th>Checkdowns</th></tr></thead><tbody>{rows.map((row) => <tr key={row.key}><td>{row.quarterback_number ?? "-"}</td><td className="metric-name">{row.display_name}</td><td>{row.practices}</td><td>{row.completions}-{row.attempts}</td><td>{row.completion_pct === null ? "-" : `${row.completion_pct}%`}</td><td>{row.on_target}</td><td className="text-emerald-300">{row.positive_reads}</td><td className="text-rose-300">{row.negative_reads}</td><td>{row.positive_timing}</td><td>{row.negative_timing}</td><td>{row.receiver_drops}</td><td>{row.checkdowns}</td></tr>)}</tbody></table>{!rows.length ? <p className="p-6 text-center text-xs text-slate-600">No quarterback rows yet.</p> : null}</div></section>;
}

function NewPracticeForm({ season, busy, onCreate }: { season: number; busy: boolean; onCreate: (payload: PracticeInput) => Promise<void> }) {
  const [title, setTitle] = useState("QB Practice");
  const [date, setDate] = useState("");
  const [type, setType] = useState("Quarterbacks");
  return <form onSubmit={async (event) => { event.preventDefault(); await onCreate({ season_year: season, title, practice_date: date || null, practice_type: type }); }} className="grid gap-3 rounded-lg border border-orange/20 bg-orange/[.04] p-4 md:grid-cols-[1fr_180px_180px_auto] md:items-end"><Field label="Practice title"><input required value={title} onChange={(event) => setTitle(event.target.value)} className="practice-input" /></Field><Field label="Date"><input type="date" value={date} onChange={(event) => setDate(event.target.value)} className="practice-input" /></Field><Field label="Type"><input value={type} onChange={(event) => setType(event.target.value)} className="practice-input" /></Field><button disabled={busy} className="rounded-md bg-orange px-4 py-2.5 text-[10px] font-black uppercase tracking-[.1em] text-[#070a0f] disabled:opacity-50">Create</button></form>;
}

function PracticeEditor({ practice, busy, onUpdate, onDelete, onCreatePlay, onUpdatePlay, onDeletePlay }: { practice: Practice; busy: boolean; onUpdate: (payload: Partial<PracticeInput>) => Promise<void>; onDelete: () => Promise<void>; onCreatePlay: (payload: PracticePlayInput) => Promise<void>; onUpdatePlay: (id: string, payload: Partial<PracticePlayInput>) => Promise<void>; onDeletePlay: (id: string) => Promise<void> }) {
  const [title, setTitle] = useState(practice.title);
  const [date, setDate] = useState(practice.practice_date ?? "");
  const [type, setType] = useState(practice.practice_type);
  const [notes, setNotes] = useState(practice.notes ?? "");
  const nextSequence = useMemo(() => Math.max(0, ...practice.plays.map((play) => play.sequence)) + 1, [practice.plays]);

  return <div>
    <form onSubmit={async (event) => { event.preventDefault(); await onUpdate({ title, practice_date: date || null, practice_type: type, notes: notes || null }); }} className="grid gap-3 border-b border-white/10 p-4 lg:grid-cols-[1fr_170px_170px_1.4fr_auto_auto] lg:items-end"><Field label="Practice title"><input required value={title} onChange={(event) => setTitle(event.target.value)} className="practice-input" /></Field><Field label="Date"><input type="date" value={date} onChange={(event) => setDate(event.target.value)} className="practice-input" /></Field><Field label="Type"><input value={type} onChange={(event) => setType(event.target.value)} className="practice-input" /></Field><Field label="Practice notes"><input value={notes} onChange={(event) => setNotes(event.target.value)} className="practice-input" placeholder="Optional" /></Field><button disabled={busy} className="practice-save">Save Practice</button><button type="button" disabled={busy} onClick={onDelete} className="practice-delete">Delete</button></form>
    <div className="grid grid-cols-2 gap-px border-b border-white/10 bg-white/10 sm:grid-cols-4 xl:grid-cols-8"><MiniMetric label="Attempts" value={practice.summary.attempts} /><MiniMetric label="Complete" value={practice.summary.completions} /><MiniMetric label="Completion" value={practice.summary.completion_pct === null ? "-" : `${practice.summary.completion_pct}%`} /><MiniMetric label="On Target" value={practice.summary.on_target} /><MiniMetric label="Positive Read" value={practice.summary.positive_reads} /><MiniMetric label="Negative Read" value={practice.summary.negative_reads} /><MiniMetric label="Positive Timing" value={practice.summary.positive_timing} /><MiniMetric label="Drops" value={practice.summary.receiver_drops} /></div>
    <div className="overflow-x-auto"><table className="practice-table min-w-[1300px]"><thead><tr><th>Play</th><th>QB #</th><th>QB Name</th><th>Intended</th><th>Result</th><th>Notes</th><th>Derived Tags</th><th>Actions</th></tr></thead><tbody>{practice.plays.map((play) => <EditablePlayRow key={play.id} play={play} busy={busy} onSave={(payload) => onUpdatePlay(play.id, payload)} onDelete={() => onDeletePlay(play.id)} />)}<NewPlayRow key={`${practice.id}-${nextSequence}`} sequence={nextSequence} busy={busy} onCreate={onCreatePlay} /></tbody></table></div>
  </div>;
}

function EditablePlayRow({ play, busy, onSave, onDelete }: { play: PracticePlay; busy: boolean; onSave: (payload: PracticePlayInput) => Promise<void>; onDelete: () => Promise<void> }) {
  const [draft, setDraft] = useState<PracticePlayInput>({ sequence: play.sequence, quarterback_number: play.quarterback_number ?? "", quarterback_name: play.quarterback_name ?? "", intended_receiver: play.intended_receiver ?? "", result: play.result, notes: play.notes ?? "" });
  const set = (field: keyof PracticePlayInput, value: string | number) => setDraft((current) => ({ ...current, [field]: value }));
  return <tr><td><input aria-label={`Play ${play.sequence} number`} type="number" min="1" value={draft.sequence} onChange={(event) => set("sequence", Number(event.target.value))} /></td><td><input aria-label={`Play ${play.sequence} quarterback number`} value={draft.quarterback_number ?? ""} onChange={(event) => set("quarterback_number", event.target.value)} /></td><td><input aria-label={`Play ${play.sequence} quarterback name`} value={draft.quarterback_name ?? ""} onChange={(event) => set("quarterback_name", event.target.value)} /></td><td><input aria-label={`Play ${play.sequence} intended receiver`} value={draft.intended_receiver ?? ""} onChange={(event) => set("intended_receiver", event.target.value)} /></td><td><ResultSelect value={draft.result} onChange={(value) => set("result", value)} /></td><td><textarea aria-label={`Play ${play.sequence} notes`} rows={2} value={draft.notes ?? ""} onChange={(event) => set("notes", event.target.value)} /></td><td><div className="flex min-w-[190px] flex-wrap gap-1">{play.tags.map((tag) => <span key={tag} className={cn("practice-tag", tag.startsWith("Negative") || tag === "Overthrow" || tag === "High ball" || tag === "Low ball" ? "negative" : "positive")}>{tag}</span>)}{!play.tags.length ? <span className="text-[10px] text-slate-700">No explicit tags</span> : null}</div></td><td><div className="flex gap-1"><button disabled={busy} onClick={() => onSave(cleanPlay(draft))} className="practice-save">Save</button><button disabled={busy} onClick={onDelete} className="practice-delete">Delete</button></div></td></tr>;
}

function NewPlayRow({ sequence, busy, onCreate }: { sequence: number; busy: boolean; onCreate: (payload: PracticePlayInput) => Promise<void> }) {
  const [draft, setDraft] = useState<PracticePlayInput>({ ...emptyPlay, sequence });
  const set = (field: keyof PracticePlayInput, value: string | number) => setDraft((current) => ({ ...current, [field]: value }));
  return <tr className="new-practice-row"><td><input aria-label="New play number" type="number" min="1" value={draft.sequence} onChange={(event) => set("sequence", Number(event.target.value))} /></td><td><input aria-label="New quarterback number" value={draft.quarterback_number ?? ""} onChange={(event) => set("quarterback_number", event.target.value)} /></td><td><input aria-label="New quarterback name" value={draft.quarterback_name ?? ""} onChange={(event) => set("quarterback_name", event.target.value)} /></td><td><input aria-label="New intended receiver" value={draft.intended_receiver ?? ""} onChange={(event) => set("intended_receiver", event.target.value)} /></td><td><ResultSelect value={draft.result} onChange={(value) => set("result", value)} /></td><td><textarea aria-label="New play notes" rows={2} value={draft.notes ?? ""} onChange={(event) => set("notes", event.target.value)} placeholder="Coaching notes" /></td><td className="text-[10px] font-bold uppercase tracking-wider text-slate-600">Tags calculate after save</td><td><button disabled={busy} onClick={async () => { await onCreate(cleanPlay(draft)); setDraft({ ...emptyPlay, sequence: draft.sequence + 1 }); }} className="practice-save">Add Play</button></td></tr>;
}

function cleanPlay(play: PracticePlayInput): PracticePlayInput {
  return { ...play, quarterback_number: play.quarterback_number?.trim() || null, quarterback_name: play.quarterback_name?.trim() || null, intended_receiver: play.intended_receiver?.trim() || null, notes: play.notes?.trim() || null };
}

function ResultSelect({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return <select aria-label="Play result" value={value} onChange={(event) => onChange(event.target.value)}><option>COMPLETE</option><option>INCOMPLETE</option><option>NO PLAY</option></select>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label><span className="mb-1.5 block text-[9px] font-black uppercase tracking-[.12em] text-slate-600">{label}</span>{children}</label>;
}

function MiniMetric({ label, value }: { label: string; value: string | number }) {
  return <div className="bg-[#090e17] px-4 py-3"><p className="text-[8px] font-bold uppercase tracking-[.12em] text-slate-600">{label}</p><p className="mt-1 text-lg font-black tabular-nums">{value}</p></div>;
}

function ChartPanel({ title, meta, children }: { title: string; meta: string; children: React.ReactNode }) {
  return <section className="analytics-panel"><div className="flex items-center justify-between border-b border-white/10 px-4 py-3"><h3 className="text-sm font-black uppercase tracking-[.12em]">{title}</h3><span className="text-[10px] font-bold uppercase tracking-wider text-slate-600">{meta}</span></div><div className="h-72 p-3">{children}</div></section>;
}

function EmptyChart() {
  return <div className="grid h-full place-items-center text-[10px] font-bold uppercase tracking-wider text-slate-700">No practice data</div>;
}
