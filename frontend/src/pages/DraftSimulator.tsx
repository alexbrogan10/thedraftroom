import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAppState } from "../context/AppContext";
import { DraftAPI } from "../services/api";
import type { SimulatePick, TradeAnalysisResponse } from "../types";
import { Card, ErrorState, Loading } from "../components/Card";
import { GradePill, PositionTag } from "../components/Badges";

export function DraftSimulator() {
  const { selectedTeam, selectedTeamId, draftYear, currentPick, setCurrentPick } = useAppState();
  const [draftedIds, setDraftedIds] = useState<number[]>([]);
  const [draftedLog, setDraftedLog] = useState<{ pick: number; pick_selection: SimulatePick }[]>([]);
  const [bestAvailable, setBestAvailable] = useState<SimulatePick[]>([]);
  const [needsSnapshot, setNeedsSnapshot] = useState<string[]>([]);
  const [remainingCount, setRemainingCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [targetId, setTargetId] = useState<number | null>(null);
  const [altPicksInput, setAltPicksInput] = useState("");
  const [tradeResult, setTradeResult] = useState<TradeAnalysisResponse | null>(null);

  const runSimulation = () => {
    if (!selectedTeamId) return;
    setLoading(true);
    setError(null);
    DraftAPI.simulate({
      team_id: selectedTeamId,
      draft_year: draftYear,
      pick_number: currentPick,
      drafted_prospect_ids: draftedIds,
    })
      .then((res) => {
        setBestAvailable(res.best_available);
        setNeedsSnapshot(res.team_needs_snapshot);
        setRemainingCount(res.remaining_prospect_count);
        setTargetId(res.best_available[0]?.prospect_id ?? null);
      })
      .catch(() => setError("Could not run the simulation."))
      .finally(() => setLoading(false));
  };

  useEffect(runSimulation, [selectedTeamId, draftYear, currentPick, draftedIds]);

  function draftPlayer(pick: SimulatePick) {
    setDraftedIds((ids) => [...ids, pick.prospect_id]);
    setDraftedLog((log) => [...log, { pick: currentPick, pick_selection: pick }]);
    setCurrentPick(currentPick + 1);
  }

  function resetSimulation() {
    setDraftedIds([]);
    setDraftedLog([]);
  }

  function runTradeAnalysis() {
    if (!targetId) return;
    const alternatives = altPicksInput
      .split(",")
      .map((s) => Number(s.trim()))
      .filter((n) => !Number.isNaN(n) && n > 0);
    DraftAPI.tradeAnalysis({
      draft_year: draftYear,
      current_pick: currentPick,
      target_prospect_id: targetId,
      alternative_picks: alternatives,
    })
      .then(setTradeResult)
      .catch(() => setTradeResult(null));
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--color-text)]">Draft Simulator</h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Simulating for <span className="text-[var(--color-text)]">{selectedTeam?.name ?? "—"}</span>, on the clock
            at pick <span className="font-mono text-[var(--color-accent)]">#{currentPick}</span>.
          </p>
        </div>
        <button
          onClick={resetSimulation}
          className="rounded border border-[var(--color-border)] bg-[var(--color-panel-raised)] px-3 py-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
        >
          Reset Simulation
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card title="Team Needs Snapshot" className="lg:col-span-1">
          <div className="flex flex-wrap gap-2">
            {needsSnapshot.map((n) => (
              <PositionTag key={n} position={n} />
            ))}
          </div>
          <p className="mt-3 text-xs text-[var(--color-text-faint)]">{remainingCount} prospects remain on the board.</p>
        </Card>

        <Card title="Draft History" className="lg:col-span-2">
          {draftedLog.length === 0 ? (
            <p className="text-sm text-[var(--color-text-faint)]">No selections made yet.</p>
          ) : (
            <ol className="space-y-1 text-sm">
              {draftedLog.map((entry) => (
                <li key={entry.pick} className="flex items-center justify-between border-b border-[var(--color-border-subtle)] py-1 last:border-0">
                  <span className="font-mono text-[var(--color-text-faint)]">#{entry.pick}</span>
                  <Link to={`/prospects/${entry.pick_selection.prospect_id}`} className="text-[var(--color-text)] hover:underline">
                    {entry.pick_selection.name}
                  </Link>
                  <PositionTag position={entry.pick_selection.position} />
                </li>
              ))}
            </ol>
          )}
        </Card>
      </div>

      {loading && <Loading label="Finding best available prospects..." />}
      {error && <ErrorState message={error} />}

      {!loading && !error && (
        <Card title={`Best Available at #${currentPick}`}>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {bestAvailable.map((p) => (
              <div key={p.prospect_id} className="flex flex-col justify-between rounded border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-3">
                <div>
                  <div className="flex items-center justify-between">
                    <PositionTag position={p.position} />
                    <GradePill value={p.draft_grade} />
                  </div>
                  <Link to={`/prospects/${p.prospect_id}`} className="mt-2 block text-sm font-medium text-[var(--color-text)] hover:underline">
                    {p.name}
                  </Link>
                  <div className="mt-1 text-[11px] text-[var(--color-text-faint)]">
                    Fit {p.team_fit.toFixed(0)} · Value {p.value_score.toFixed(0)} · Risk {p.risk_score.toFixed(0)}
                  </div>
                </div>
                <button
                  onClick={() => draftPlayer(p)}
                  className="mt-3 rounded bg-[var(--color-accent)] px-2 py-1.5 text-xs font-semibold text-black hover:opacity-90"
                >
                  Select Player
                </button>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card title="Trade-Up / Trade-Down Analysis" subtitle="Evaluate the cost and availability odds of moving in the draft order">
        <div className="mb-4 flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-xs text-[var(--color-text-faint)]">
            Target Prospect
            <select
              value={targetId ?? ""}
              onChange={(e) => setTargetId(Number(e.target.value))}
              className="rounded border border-[var(--color-border)] bg-[var(--color-panel-raised)] px-2 py-1.5 text-sm text-[var(--color-text)]"
            >
              {bestAvailable.map((p) => (
                <option key={p.prospect_id} value={p.prospect_id}>
                  {p.name} ({p.position})
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-[var(--color-text-faint)]">
            Alternative Pick Numbers (comma-separated, earlier than #{currentPick})
            <input
              value={altPicksInput}
              onChange={(e) => setAltPicksInput(e.target.value)}
              placeholder="e.g. 8, 5"
              className="w-56 rounded border border-[var(--color-border)] bg-[var(--color-panel-raised)] px-2 py-1.5 text-sm text-[var(--color-text)]"
            />
          </label>
          <button
            onClick={runTradeAnalysis}
            className="rounded bg-[var(--color-turf)] px-3 py-1.5 text-sm font-medium text-white hover:opacity-90"
          >
            Analyze Trade
          </button>
        </div>

        {tradeResult && (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {[tradeResult.current_pick_option, ...tradeResult.trade_up_options].map((opt) => (
              <div key={opt.label} className="rounded border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-3">
                <div className="text-sm font-medium text-[var(--color-text)]">{opt.label}</div>
                <div className="mt-1 text-xs text-[var(--color-text-muted)]">
                  Probability {tradeResult.target_name} is still available:
                </div>
                <div className="font-mono text-xl text-[var(--color-accent)]">
                  {(opt.probability_target_available * 100).toFixed(0)}%
                </div>
                <div className="mt-1 text-[11px] text-[var(--color-text-faint)]">{opt.cost_description}</div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
