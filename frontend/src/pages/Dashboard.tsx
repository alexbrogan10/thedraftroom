import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAppState } from "../context/AppContext";
import { DraftAPI, TeamsAPI } from "../services/api";
import type { BoardEntry, TeamNeed } from "../types";
import { Card, ErrorState, Loading } from "../components/Card";
import { GradePill, PositionTag, RiskBadge } from "../components/Badges";

function ProspectMiniRow({ entry, rightLabel, rightValue }: { entry: BoardEntry; rightLabel: string; rightValue: string }) {
  return (
    <Link
      to={`/prospects/${entry.prospect_id}`}
      className="flex items-center justify-between rounded px-2 py-2 hover:bg-[var(--color-panel-raised)]"
    >
      <div className="flex items-center gap-3">
        <PositionTag position={entry.position} />
        <div>
          <div className="text-sm font-medium text-[var(--color-text)]">{entry.name}</div>
          <div className="text-xs text-[var(--color-text-faint)]">{entry.college}</div>
        </div>
      </div>
      <div className="text-right">
        <div className="text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">{rightLabel}</div>
        <div className="font-mono text-sm text-[var(--color-text)]">{rightValue}</div>
      </div>
    </Link>
  );
}

export function Dashboard() {
  const { selectedTeam, selectedTeamId, draftYear, currentPick } = useAppState();
  const [board, setBoard] = useState<BoardEntry[]>([]);
  const [teamBoard, setTeamBoard] = useState<BoardEntry[]>([]);
  const [needs, setNeeds] = useState<TeamNeed[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!selectedTeamId) return;
    setLoading(true);
    setError(null);
    Promise.all([
      DraftAPI.board(draftYear, 100),
      TeamsAPI.draftBoard(selectedTeamId, draftYear, 50),
      TeamsAPI.needs(selectedTeamId, draftYear),
    ])
      .then(([b, tb, n]) => {
        setBoard(b);
        setTeamBoard(tb);
        setNeeds(n.sort((a, c) => c.need_score - a.need_score).slice(0, 5));
      })
      .catch(() => setError("Could not load dashboard data. Is the API running?"))
      .finally(() => setLoading(false));
  }, [selectedTeamId, draftYear]);

  if (loading) return <Loading label="Assembling front office dashboard..." />;
  if (error) return <ErrorState message={error} />;

  const topProspects = [...board].sort((a, b) => b.draft_grade - a.draft_grade).slice(0, 5);
  const biggestValues = [...board]
    .filter((b) => b.value_score >= 60)
    .sort((a, b) => b.value_score - a.value_score)
    .slice(0, 5);
  const highestRisk = [...board].sort((a, b) => b.risk_score - a.risk_score).slice(0, 5);
  const recommendations = [...teamBoard].sort((a, b) => (b.team_fit ?? 0) - (a.team_fit ?? 0)).slice(0, 5);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-[var(--color-text)]">The Draft Room</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Selected Team: <span className="text-[var(--color-text)]">{selectedTeam?.name ?? "—"}</span> &nbsp;·&nbsp;
          Current Pick: <span className="font-mono text-[var(--color-accent)]">#{currentPick}</span> &nbsp;·&nbsp;
          Draft Class: <span className="text-[var(--color-text)]">{draftYear}</span>
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card title="Top Available Prospects" subtitle="League-wide Draft Grade leaders">
          <div className="divide-y divide-[var(--color-border-subtle)]">
            {topProspects.map((p) => (
              <ProspectMiniRow key={p.prospect_id} entry={p} rightLabel="Grade" rightValue={p.draft_grade.toFixed(1)} />
            ))}
          </div>
        </Card>

        <Card title="Draft Recommendations" subtitle={`Best available for ${selectedTeam?.abbreviation ?? "—"} at #${currentPick}`}>
          <div className="divide-y divide-[var(--color-border-subtle)]">
            {recommendations.map((p) => (
              <ProspectMiniRow key={p.prospect_id} entry={p} rightLabel="Team Fit" rightValue={(p.team_fit ?? 0).toFixed(0)} />
            ))}
          </div>
        </Card>

        <Card title="Biggest Values" subtitle="Analytical rank well ahead of expected draft range">
          <div className="divide-y divide-[var(--color-border-subtle)]">
            {biggestValues.length === 0 && (
              <p className="p-2 text-sm text-[var(--color-text-faint)]">No standout value differentials in this class.</p>
            )}
            {biggestValues.map((p) => (
              <ProspectMiniRow key={p.prospect_id} entry={p} rightLabel="Value" rightValue={p.value_score.toFixed(0)} />
            ))}
          </div>
        </Card>

        <Card title="Highest Risk" subtitle="Largest overall Risk Score in the class">
          <div className="divide-y divide-[var(--color-border-subtle)]">
            {highestRisk.map((p) => (
              <div key={p.prospect_id} className="flex items-center justify-between px-2 py-2">
                <Link to={`/prospects/${p.prospect_id}`} className="flex items-center gap-3 hover:underline">
                  <PositionTag position={p.position} />
                  <span className="text-sm text-[var(--color-text)]">{p.name}</span>
                </Link>
                <RiskBadge level={p.risk_level} />
              </div>
            ))}
          </div>
        </Card>

        <Card title={`${selectedTeam?.name ?? "Team"} — Top Needs`} subtitle={`${draftYear} season need score`} className="lg:col-span-2">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            {needs.map((n) => (
              <div key={n.position} className="rounded border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-3 text-center">
                <div className="text-xs text-[var(--color-text-faint)]">{n.position}</div>
                <GradePill value={n.need_score} />
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
