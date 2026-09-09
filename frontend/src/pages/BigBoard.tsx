import { Fragment, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAppState } from "../context/AppContext";
import { DraftAPI, TeamsAPI } from "../services/api";
import type { BoardEntry } from "../types";
import { Card, ErrorState, Loading } from "../components/Card";
import { GradePill, PositionTag, RiskBadge } from "../components/Badges";

export function BigBoard() {
  const { selectedTeam, selectedTeamId, draftYear } = useAppState();
  const [mode, setMode] = useState<"league" | "team">("league");
  const [rows, setRows] = useState<BoardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    const request =
      mode === "league"
        ? DraftAPI.board(draftYear, 150)
        : selectedTeamId
          ? TeamsAPI.draftBoard(selectedTeamId, draftYear, 150)
          : Promise.resolve([]);
    request
      .then(setRows)
      .catch(() => setError("Could not load the big board."))
      .finally(() => setLoading(false));
  }, [mode, selectedTeamId, draftYear]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--color-text)]">The Big Board</h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            {mode === "league"
              ? "League-wide analytical ranking, independent of any single team's needs."
              : `Reordered for ${selectedTeam?.name ?? "the selected team"} — talent blended with organizational fit.`}
          </p>
        </div>
        <div className="flex rounded border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-0.5 text-sm">
          <button
            onClick={() => setMode("league")}
            className={`rounded px-3 py-1 ${mode === "league" ? "bg-[var(--color-accent)] text-black" : "text-[var(--color-text-muted)]"}`}
          >
            League Board
          </button>
          <button
            onClick={() => setMode("team")}
            className={`rounded px-3 py-1 ${mode === "team" ? "bg-[var(--color-accent)] text-black" : "text-[var(--color-text-muted)]"}`}
          >
            Team Board
          </button>
        </div>
      </div>

      {loading && <Loading label="Building board..." />}
      {error && <ErrorState message={error} />}

      {!loading && !error && (
        <Card className="overflow-hidden !p-0">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-[var(--color-border)] bg-[var(--color-panel-raised)] text-[11px] uppercase tracking-wide text-[var(--color-text-faint)]">
              <tr>
                <th className="px-3 py-2">#</th>
                {mode === "team" && <th className="px-3 py-2">League #</th>}
                <th className="px-3 py-2">Prospect</th>
                <th className="px-3 py-2">Pos</th>
                <th className="px-3 py-2">College</th>
                <th className="px-3 py-2">Draft Grade</th>
                {mode === "team" && <th className="px-3 py-2">Team Fit</th>}
                <th className="px-3 py-2">Value</th>
                <th className="px-3 py-2">Risk</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <Fragment key={r.prospect_id}>
                  <tr
                    className="cursor-pointer border-b border-[var(--color-border-subtle)] hover:bg-[var(--color-panel-raised)]"
                    onClick={() => setExpanded(expanded === r.prospect_id ? null : r.prospect_id)}
                  >
                    <td className="px-3 py-2 font-mono text-[var(--color-text-muted)]">
                      {mode === "team" ? r.team_rank : r.league_rank}
                    </td>
                    {mode === "team" && <td className="px-3 py-2 font-mono text-[var(--color-text-faint)]">{r.league_rank}</td>}
                    <td className="px-3 py-2">
                      <Link to={`/prospects/${r.prospect_id}`} className="font-medium text-[var(--color-text)] hover:underline" onClick={(e) => e.stopPropagation()}>
                        {r.name}
                      </Link>
                    </td>
                    <td className="px-3 py-2">
                      <PositionTag position={r.position} />
                    </td>
                    <td className="px-3 py-2 text-[var(--color-text-muted)]">{r.college}</td>
                    <td className="px-3 py-2">
                      <GradePill value={r.draft_grade} />
                    </td>
                    {mode === "team" && (
                      <td className="px-3 py-2 font-mono text-[var(--color-text)]">{(r.team_fit ?? 0).toFixed(0)}</td>
                    )}
                    <td className="px-3 py-2 font-mono text-[var(--color-text)]">{r.value_score.toFixed(0)}</td>
                    <td className="px-3 py-2">
                      <RiskBadge level={r.risk_level} />
                    </td>
                  </tr>
                  {expanded === r.prospect_id && r.reason && (
                    <tr className="border-b border-[var(--color-border-subtle)] bg-[var(--color-panel-raised)]/60">
                      <td colSpan={mode === "team" ? 8 : 6} className="px-3 py-2 text-xs text-[var(--color-text-muted)]">
                        {r.reason}
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
