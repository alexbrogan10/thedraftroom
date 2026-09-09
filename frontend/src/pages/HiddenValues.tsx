import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAppState } from "../context/AppContext";
import { DraftAPI } from "../services/api";
import type { BoardEntry } from "../types";
import { Card, ErrorState, Loading } from "../components/Card";
import { GradePill, PositionTag, ValueBadge } from "../components/Badges";

export function HiddenValues() {
  const { draftYear } = useAppState();
  const [rows, setRows] = useState<BoardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    DraftAPI.board(draftYear, 300)
      .then(setRows)
      .catch(() => setError("Could not load the value analysis."))
      .finally(() => setLoading(false));
  }, [draftYear]);

  if (loading) return <Loading label="Scanning the class for value..." />;
  if (error) return <ErrorState message={error} />;

  const values = [...rows]
    .filter((r) => r.expected_rank != null)
    .sort((a, b) => (b.expected_rank! - b.league_rank) - (a.expected_rank! - a.league_rank));

  const reaches = [...values].reverse();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-[var(--color-text)]">Hidden Value Finder</h1>
        <p className="mt-1 max-w-3xl text-sm text-[var(--color-text-muted)]">
          Compares each prospect's league-wide analytical rank against the expected draft range implied by
          consensus scouting projections. A positive differential means the model identifies the prospect as
          potentially undervalued relative to where it is expected to be drafted — not a guarantee of outcome.
        </p>
      </div>

      <Card title="Potential Values" subtitle="Analytical rank ahead of expected draft range">
        <ValueTable rows={values.filter((r) => (r.expected_rank! - r.league_rank) > 0).slice(0, 15)} />
      </Card>

      <Card title="Potential Reaches" subtitle="Analytical rank behind expected draft range">
        <ValueTable rows={reaches.filter((r) => (r.expected_rank! - r.league_rank) < 0).slice(0, 15)} />
      </Card>
    </div>
  );
}

function ValueTable({ rows }: { rows: BoardEntry[] }) {
  if (rows.length === 0) {
    return <p className="text-sm text-[var(--color-text-faint)]">No prospects in this category.</p>;
  }
  return (
    <table className="w-full text-left text-sm">
      <thead className="text-[11px] uppercase tracking-wide text-[var(--color-text-faint)]">
        <tr>
          <th className="px-2 py-1.5">Prospect</th>
          <th className="px-2 py-1.5">Pos</th>
          <th className="px-2 py-1.5">Analytical Rank</th>
          <th className="px-2 py-1.5">Expected Range</th>
          <th className="px-2 py-1.5">Differential</th>
          <th className="px-2 py-1.5">Grade</th>
          <th className="px-2 py-1.5">Classification</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => {
          const diff = Math.round((r.expected_rank ?? 0) - r.league_rank);
          return (
            <tr key={r.prospect_id} className="border-t border-[var(--color-border-subtle)] hover:bg-[var(--color-panel-raised)]">
              <td className="px-2 py-1.5">
                <Link to={`/prospects/${r.prospect_id}`} className="font-medium text-[var(--color-text)] hover:underline">
                  {r.name}
                </Link>
              </td>
              <td className="px-2 py-1.5">
                <PositionTag position={r.position} />
              </td>
              <td className="px-2 py-1.5 font-mono">#{r.league_rank}</td>
              <td className="px-2 py-1.5 font-mono text-[var(--color-text-muted)]">#{Math.round(r.expected_rank ?? 0)}</td>
              <td className={`px-2 py-1.5 font-mono ${diff > 0 ? "text-[var(--color-risk-low)]" : "text-[var(--color-risk-high)]"}`}>
                {diff > 0 ? "+" : ""}
                {diff}
              </td>
              <td className="px-2 py-1.5">
                <GradePill value={r.draft_grade} />
              </td>
              <td className="px-2 py-1.5">
                <ValueBadge classification={r.value_classification} icon={r.value_icon} />
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
