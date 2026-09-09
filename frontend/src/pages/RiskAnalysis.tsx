import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAppState } from "../context/AppContext";
import { DraftAPI } from "../services/api";
import type { BoardEntry } from "../types";
import { Card, ErrorState, Loading } from "../components/Card";
import { GradePill, PositionTag, RiskBadge } from "../components/Badges";

export function RiskAnalysis() {
  const { draftYear } = useAppState();
  const [rows, setRows] = useState<BoardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [levelFilter, setLevelFilter] = useState<string>("ALL");

  useEffect(() => {
    setLoading(true);
    DraftAPI.board(draftYear, 300)
      .then(setRows)
      .catch(() => setError("Could not load risk data."))
      .finally(() => setLoading(false));
  }, [draftYear]);

  if (loading) return <Loading label="Assessing risk across the class..." />;
  if (error) return <ErrorState message={error} />;

  const sorted = [...rows]
    .filter((r) => levelFilter === "ALL" || r.risk_level.includes(levelFilter))
    .sort((a, b) => b.risk_score - a.risk_score);

  const distribution = {
    LOWER: rows.filter((r) => r.risk_level.includes("LOWER")).length,
    MODERATE: rows.filter((r) => r.risk_level.includes("MODERATE")).length,
    HIGHER: rows.filter((r) => r.risk_level.includes("HIGHER")).length,
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-[var(--color-text)]">Draft Risk Analyzer</h1>
        <p className="mt-1 max-w-3xl text-sm text-[var(--color-text-muted)]">
          Overall Risk Score blends production sample size/completeness, cross-source projection spread,
          strength of college competition, athletic-testing dependency, and positional projection volatility.
          See a prospect's profile for the full factor breakdown. Prospects are described as lower/moderate/
          higher-risk — never as "busts."
        </p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {(["LOWER", "MODERATE", "HIGHER"] as const).map((level) => (
          <button
            key={level}
            onClick={() => setLevelFilter(levelFilter === level ? "ALL" : level)}
            className={`rounded-lg border p-4 text-left transition-colors ${
              levelFilter === level
                ? "border-[var(--color-accent)] bg-[var(--color-panel-raised)]"
                : "border-[var(--color-border)] bg-[var(--color-panel)] hover:bg-[var(--color-panel-raised)]"
            }`}
          >
            <div className="text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">{level} Risk</div>
            <div className="mt-1 text-2xl font-mono text-[var(--color-text)]">{distribution[level]}</div>
          </button>
        ))}
      </div>

      <Card className="overflow-hidden !p-0" title={`${sorted.length} Prospects`}>
        <table className="w-full text-left text-sm">
          <thead className="border-b border-[var(--color-border)] bg-[var(--color-panel-raised)] text-[11px] uppercase tracking-wide text-[var(--color-text-faint)]">
            <tr>
              <th className="px-3 py-2">Prospect</th>
              <th className="px-3 py-2">Pos</th>
              <th className="px-3 py-2">College</th>
              <th className="px-3 py-2">Grade</th>
              <th className="px-3 py-2">Risk Score</th>
              <th className="px-3 py-2">Risk Level</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((r) => (
              <tr key={r.prospect_id} className="border-b border-[var(--color-border-subtle)] hover:bg-[var(--color-panel-raised)]">
                <td className="px-3 py-2">
                  <Link to={`/prospects/${r.prospect_id}`} className="font-medium text-[var(--color-text)] hover:underline">
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
                <td className="px-3 py-2 font-mono text-[var(--color-text)]">{r.risk_score.toFixed(0)}</td>
                <td className="px-3 py-2">
                  <RiskBadge level={r.risk_level} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
