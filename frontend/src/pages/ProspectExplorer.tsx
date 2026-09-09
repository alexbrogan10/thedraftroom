import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAppState } from "../context/AppContext";
import { ProspectsAPI, type ProspectListParams } from "../services/api";
import type { ProspectSummary } from "../types";
import { Card, ErrorState, Loading } from "../components/Card";
import { GradePill, PositionTag, RiskBadge } from "../components/Badges";

const POSITIONS = ["QB", "RB", "WR", "TE", "OT", "IOL", "EDGE", "IDL", "LB", "CB", "S"];
const SORT_OPTIONS: { value: ProspectListParams["sort_by"]; label: string }[] = [
  { value: "draft_grade", label: "Draft Grade" },
  { value: "value_score", label: "Value" },
  { value: "risk_score", label: "Risk" },
  { value: "projected_pick", label: "Projected Pick" },
];

export function ProspectExplorer() {
  const { draftYear } = useAppState();
  const [rows, setRows] = useState<ProspectSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [position, setPosition] = useState("");
  const [college, setCollege] = useState("");
  const [minGrade, setMinGrade] = useState<number | "">("");
  const [maxRisk, setMaxRisk] = useState<number | "">("");
  const [sortBy, setSortBy] = useState<ProspectListParams["sort_by"]>("draft_grade");

  useEffect(() => {
    setLoading(true);
    setError(null);
    const params: ProspectListParams = {
      draft_year: draftYear,
      position: position || undefined,
      college: college || undefined,
      min_draft_grade: minGrade === "" ? undefined : minGrade,
      max_risk: maxRisk === "" ? undefined : maxRisk,
      sort_by: sortBy,
      descending: sortBy !== "risk_score" && sortBy !== "projected_pick",
      limit: 300,
    };
    ProspectsAPI.list(params)
      .then(setRows)
      .catch(() => setError("Could not load prospects."))
      .finally(() => setLoading(false));
  }, [draftYear, position, college, minGrade, maxRisk, sortBy]);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-[var(--color-text)]">Prospect Explorer</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">Search and filter the full {draftYear} prospect database.</p>
      </div>

      <Card>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <label className="flex flex-col gap-1 text-xs text-[var(--color-text-faint)]">
            Position
            <select
              value={position}
              onChange={(e) => setPosition(e.target.value)}
              className="rounded border border-[var(--color-border)] bg-[var(--color-panel-raised)] px-2 py-1.5 text-sm text-[var(--color-text)]"
            >
              <option value="">All</option>
              {POSITIONS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-[var(--color-text-faint)]">
            College
            <input
              value={college}
              onChange={(e) => setCollege(e.target.value)}
              placeholder="e.g. Georgia"
              className="rounded border border-[var(--color-border)] bg-[var(--color-panel-raised)] px-2 py-1.5 text-sm text-[var(--color-text)]"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-[var(--color-text-faint)]">
            Min Draft Grade
            <input
              type="number"
              value={minGrade}
              onChange={(e) => setMinGrade(e.target.value === "" ? "" : Number(e.target.value))}
              className="rounded border border-[var(--color-border)] bg-[var(--color-panel-raised)] px-2 py-1.5 text-sm text-[var(--color-text)]"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-[var(--color-text-faint)]">
            Max Risk Score
            <input
              type="number"
              value={maxRisk}
              onChange={(e) => setMaxRisk(e.target.value === "" ? "" : Number(e.target.value))}
              className="rounded border border-[var(--color-border)] bg-[var(--color-panel-raised)] px-2 py-1.5 text-sm text-[var(--color-text)]"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-[var(--color-text-faint)] lg:col-span-2">
            Sort By
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as ProspectListParams["sort_by"])}
              className="rounded border border-[var(--color-border)] bg-[var(--color-panel-raised)] px-2 py-1.5 text-sm text-[var(--color-text)]"
            >
              {SORT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </Card>

      {loading && <Loading label="Searching prospects..." />}
      {error && <ErrorState message={error} />}

      {!loading && !error && (
        <Card className="overflow-hidden !p-0">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-[var(--color-border)] bg-[var(--color-panel-raised)] text-[11px] uppercase tracking-wide text-[var(--color-text-faint)]">
              <tr>
                <th className="px-3 py-2">Prospect</th>
                <th className="px-3 py-2">Pos</th>
                <th className="px-3 py-2">College</th>
                <th className="px-3 py-2">Age</th>
                <th className="px-3 py-2">Class</th>
                <th className="px-3 py-2">Grade</th>
                <th className="px-3 py-2">Value</th>
                <th className="px-3 py-2">Risk</th>
                <th className="px-3 py-2">Proj. Pick</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.id} className="border-b border-[var(--color-border-subtle)] hover:bg-[var(--color-panel-raised)]">
                  <td className="px-3 py-2">
                    <Link to={`/prospects/${p.id}`} className="font-medium text-[var(--color-text)] hover:underline">
                      {p.name}
                    </Link>
                  </td>
                  <td className="px-3 py-2">
                    <PositionTag position={p.position} />
                  </td>
                  <td className="px-3 py-2 text-[var(--color-text-muted)]">{p.college}</td>
                  <td className="px-3 py-2 text-[var(--color-text-muted)]">{p.age ?? "—"}</td>
                  <td className="px-3 py-2 text-[var(--color-text-muted)]">{p.class_year ?? "—"}</td>
                  <td className="px-3 py-2">
                    <GradePill value={p.draft_grade} />
                  </td>
                  <td className="px-3 py-2 font-mono text-[var(--color-text)]">{p.value_score.toFixed(0)}</td>
                  <td className="px-3 py-2">
                    <RiskBadge level={p.risk_level} />
                  </td>
                  <td className="px-3 py-2 font-mono text-[var(--color-text-muted)]">
                    {p.projected_pick ? `#${Math.round(p.projected_pick)}` : "—"}
                  </td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={9} className="px-3 py-6 text-center text-sm text-[var(--color-text-faint)]">
                    No prospects match these filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
