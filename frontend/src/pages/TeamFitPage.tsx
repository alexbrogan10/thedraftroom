import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAppState } from "../context/AppContext";
import { TeamsAPI } from "../services/api";
import type { BoardEntry, TeamNeed } from "../types";
import { Card, ErrorState, Loading } from "../components/Card";
import { GradePill, PositionTag } from "../components/Badges";

export function TeamFitPage() {
  const { selectedTeam, selectedTeamId, draftYear } = useAppState();
  const [rows, setRows] = useState<BoardEntry[]>([]);
  const [needs, setNeeds] = useState<TeamNeed[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedTeamId) return;
    setLoading(true);
    Promise.all([TeamsAPI.draftBoard(selectedTeamId, draftYear, 200), TeamsAPI.needs(selectedTeamId, draftYear)])
      .then(([b, n]) => {
        setRows([...b].sort((x, y) => (y.team_fit ?? 0) - (x.team_fit ?? 0)));
        setNeeds(n);
      })
      .catch(() => setError("Could not load team fit data."))
      .finally(() => setLoading(false));
  }, [selectedTeamId, draftYear]);

  if (loading) return <Loading label="Evaluating organizational fit..." />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-[var(--color-text)]">Team Fit Engine</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          {selectedTeam?.name ?? "Selected team"}'s fit score for every {draftYear} prospect — current need, future
          need, roster depth, scheme fit, development timeline, and positional value. See a prospect's profile for
          the full explained breakdown.
        </p>
      </div>

      <Card title="Positional Needs by Season">
        <div className="flex flex-wrap gap-4">
          {[...new Set(needs.map((n) => n.season))].sort().map((season) => (
            <div key={season} className="min-w-[180px] flex-1">
              <div className="mb-1 text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">{season}</div>
              <div className="space-y-1">
                {needs
                  .filter((n) => n.season === season)
                  .sort((a, b) => b.need_score - a.need_score)
                  .slice(0, 5)
                  .map((n) => (
                    <div key={n.position} className="flex items-center justify-between rounded bg-[var(--color-panel-raised)] px-2 py-1 text-xs">
                      <span className="text-[var(--color-text-muted)]">{n.position}</span>
                      <span className="font-mono text-[var(--color-text)]">{n.need_score.toFixed(0)}</span>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card className="overflow-hidden !p-0" title="Prospects Ranked by Team Fit">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-[var(--color-border)] bg-[var(--color-panel-raised)] text-[11px] uppercase tracking-wide text-[var(--color-text-faint)]">
            <tr>
              <th className="px-3 py-2">Prospect</th>
              <th className="px-3 py-2">Pos</th>
              <th className="px-3 py-2">League Rank</th>
              <th className="px-3 py-2">Draft Grade</th>
              <th className="px-3 py-2">Team Fit</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 40).map((r) => (
              <tr key={r.prospect_id} className="border-b border-[var(--color-border-subtle)] hover:bg-[var(--color-panel-raised)]">
                <td className="px-3 py-2">
                  <Link to={`/prospects/${r.prospect_id}`} className="font-medium text-[var(--color-text)] hover:underline">
                    {r.name}
                  </Link>
                </td>
                <td className="px-3 py-2">
                  <PositionTag position={r.position} />
                </td>
                <td className="px-3 py-2 font-mono text-[var(--color-text-faint)]">#{r.league_rank}</td>
                <td className="px-3 py-2">
                  <GradePill value={r.draft_grade} />
                </td>
                <td className="px-3 py-2">
                  <GradePill value={r.team_fit ?? 0} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
