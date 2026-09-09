import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useAppState } from "../context/AppContext";
import { ProspectsAPI } from "../services/api";
import type {
  HistoricalComparison,
  OutcomePrediction,
  ProspectAnalytics,
  ProspectDetail,
  TeamFit as TeamFitType,
} from "../types";
import { Card, ErrorState, Loading } from "../components/Card";
import { GradePill, PositionTag, RiskBadge, ValueBadge } from "../components/Badges";

const COMPONENT_LABELS: Record<string, string> = {
  production: "Production",
  athletic_profile: "Athleticism",
  age_experience: "Age Profile",
  position_value: "Position Value",
  nfl_projection: "NFL Projection",
  risk_adjustment: "Risk Adjustment",
};

const RISK_LABELS: Record<string, string> = {
  production_risk: "Production Risk",
  projection_risk: "Projection Risk",
  competition_risk: "Competition Risk",
  athletic_dependency_risk: "Athletic Dependency",
  position_risk: "Position Risk",
};

const COMBINE_LABELS: Record<string, string> = {
  forty_yard_dash: "40-Yard Dash",
  vertical_jump: "Vertical Jump (in)",
  broad_jump: "Broad Jump (in)",
  bench_press: "Bench Press (reps)",
  three_cone: "3-Cone Drill",
  shuttle: "Shuttle",
};

function riskColorFor(level: string) {
  const l = level.toUpperCase();
  if (l === "LOW") return "#3fae66";
  if (l === "HIGH") return "#c0523f";
  return "#d8a53d";
}

export function ProspectProfile() {
  const { id } = useParams();
  const prospectId = Number(id);
  const { selectedTeamId, selectedTeam } = useAppState();

  const [detail, setDetail] = useState<ProspectDetail | null>(null);
  const [analytics, setAnalytics] = useState<ProspectAnalytics | null>(null);
  const [teamFit, setTeamFit] = useState<TeamFitType | null>(null);
  const [comparisons, setComparisons] = useState<HistoricalComparison[]>([]);
  const [outcome, setOutcome] = useState<OutcomePrediction | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!prospectId) return;
    setLoading(true);
    setError(null);
    Promise.all([
      ProspectsAPI.get(prospectId),
      ProspectsAPI.analytics(prospectId),
      ProspectsAPI.comparisons(prospectId),
      ProspectsAPI.outcomePrediction(prospectId),
    ])
      .then(([d, a, c, o]) => {
        setDetail(d);
        setAnalytics(a);
        setComparisons(c);
        setOutcome(o);
      })
      .catch(() => setError("Could not load this prospect."))
      .finally(() => setLoading(false));
  }, [prospectId]);

  useEffect(() => {
    if (!prospectId || !selectedTeamId) return;
    ProspectsAPI.teamFit(prospectId, selectedTeamId).then(setTeamFit).catch(() => setTeamFit(null));
  }, [prospectId, selectedTeamId]);

  if (loading) return <Loading label="Loading prospect profile..." />;
  if (error || !detail || !analytics) return <ErrorState message={error ?? "Prospect not found."} />;

  const gradeData = Object.entries(analytics.draft_grade.components).map(([key, value]) => ({
    key,
    label: COMPONENT_LABELS[key] ?? key,
    value,
    note: analytics.draft_grade.notes[key],
  }));

  const riskData = Object.entries(analytics.risk.factors).map(([key, factor]) => ({
    key,
    label: RISK_LABELS[key] ?? key,
    value: factor.score,
    level: factor.level,
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold text-[var(--color-text)]">{detail.name}</h1>
            <PositionTag position={detail.position} />
          </div>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            {detail.college} · {detail.class_year ?? "—"} · Age {detail.age ?? "—"} · Class of {detail.draft_year}
          </p>
        </div>
        <div className="text-right">
          <div className="text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">Draft Grade</div>
          <div className="text-3xl">
            <GradePill value={analytics.draft_grade.score} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card title="Player Information">
          <dl className="space-y-1.5 text-sm">
            <Row label="Height" value={detail.height_inches ? `${Math.floor(detail.height_inches / 12)}'${Math.round(detail.height_inches % 12)}"` : "—"} />
            <Row label="Weight" value={detail.weight_lbs ? `${detail.weight_lbs} lbs` : "—"} />
            <Row label="College" value={detail.college} />
            <Row label="Class" value={detail.class_year ?? "—"} />
            <Row label="Draft Year" value={String(detail.draft_year)} />
          </dl>
        </Card>

        <Card title="Athletic Profile" subtitle="NFL Combine / Pro Day testing">
          {detail.combine ? (
            <dl className="space-y-1.5 text-sm">
              {Object.entries(COMBINE_LABELS).map(([key, label]) => {
                const v = detail.combine?.[key as keyof typeof detail.combine];
                return <Row key={key} label={label} value={v != null ? String(v) : "—"} />;
              })}
            </dl>
          ) : (
            <p className="text-sm text-[var(--color-text-faint)]">No testing data available.</p>
          )}
        </Card>

        <Card title="College Production" subtitle={`${detail.position}-specific statistics`}>
          {detail.statistics.length > 0 ? (
            <dl className="space-y-1.5 text-sm">
              {detail.statistics.map((s) => (
                <Row key={s.metric_name} label={s.metric_name.replace(/_/g, " ")} value={String(s.metric_value)} />
              ))}
            </dl>
          ) : (
            <p className="text-sm text-[var(--color-text-faint)]">No production data available.</p>
          )}
        </Card>
      </div>

      <Card title="Draft Grade Breakdown" subtitle="Every component is a percentile within the position's draft-class peer group, except Position Value (static) and Risk Adjustment (100 − Risk Score).">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={gradeData} layout="vertical" margin={{ left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#232a35" horizontal={false} />
            <XAxis type="number" domain={[0, 100]} stroke="#5b6472" fontSize={12} />
            <YAxis type="category" dataKey="label" stroke="#8b96a5" fontSize={12} width={120} />
            <Tooltip
              contentStyle={{ background: "#171c25", border: "1px solid #232a35", fontSize: 12 }}
              formatter={(value, _name, item) => [
                typeof value === "number" ? value.toFixed(1) : String(value),
                (item?.payload as { note?: string } | undefined)?.note ?? "",
              ]}
            />
            <Bar dataKey="value" radius={[0, 3, 3, 0]}>
              {gradeData.map((d) => (
                <Cell key={d.key} fill="#c9a24b" />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card title="Risk Profile" subtitle={`Overall Risk: ${analytics.risk.overall_risk}/100`}>
          <div className="mb-3">
            <RiskBadge level={analytics.risk.risk_level} />
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={riskData} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#232a35" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} stroke="#5b6472" fontSize={12} />
              <YAxis type="category" dataKey="label" stroke="#8b96a5" fontSize={12} width={130} />
              <Tooltip contentStyle={{ background: "#171c25", border: "1px solid #232a35", fontSize: 12 }} />
              <Bar dataKey="value" radius={[0, 3, 3, 0]}>
                {riskData.map((d) => (
                  <Cell key={d.key} fill={riskColorFor(d.level)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Hidden Value Assessment">
          <div className="space-y-2">
            <ValueBadge classification={analytics.value.classification} icon={analytics.value.icon} />
            <div className="text-sm text-[var(--color-text-muted)]">
              Analytical Rank: <span className="font-mono text-[var(--color-text)]">#{analytics.value.analytical_rank}</span>
              {analytics.value.expected_rank != null && (
                <>
                  {" "}
                  · Expected Range: <span className="font-mono text-[var(--color-text)]">#{analytics.value.expected_rank.toFixed(0)}</span>
                </>
              )}
            </div>
            <p className="text-sm text-[var(--color-text-muted)]">{analytics.value.explanation}</p>
          </div>
        </Card>
      </div>

      <Card title="NFL Outcome Prediction" subtitle="Model estimate from pre-draft data only — not a guarantee of outcome">
        {outcome?.available && outcome.probabilities ? (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {Object.entries({
              started: "Starter Probability",
              productive_starter: "Productive Starter Probability",
              long_term_contributor: "Long-Term Contributor Probability",
            }).map(([key, label]) => (
              <div key={key} className="rounded border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-3">
                <div className="text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">{label}</div>
                <div className="mt-1 font-mono text-2xl text-[var(--color-accent)]">
                  {outcome.probabilities?.[key] != null ? `${outcome.probabilities[key].toFixed(0)}%` : "—"}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-[var(--color-text-faint)]">{outcome?.message ?? "Model not yet trained."}</p>
        )}
        {outcome?.note && <p className="mt-3 text-[11px] text-[var(--color-text-faint)]">{outcome.note}</p>}
      </Card>

      <Card title="Team Fit" subtitle={selectedTeam ? `${selectedTeam.name} organizational fit` : "Select a team"}>
        {teamFit ? (
          <div className="space-y-3">
            <div className="text-2xl">
              <GradePill value={teamFit.score} />
              <span className="ml-2 text-sm text-[var(--color-text-faint)]">/ 100</span>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {Object.entries(teamFit.components).map(([key, value]) => (
                <div key={key} className="rounded border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-2.5">
                  <div className="text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">{key.replace(/_/g, " ")}</div>
                  <div className="font-mono text-sm text-[var(--color-text)]">{value.toFixed(0)}</div>
                  <div className="mt-1 text-[11px] text-[var(--color-text-muted)]">{teamFit.explanations[key]}</div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <Loading label="Loading team fit..." />
        )}
      </Card>

      <Card title="Historical Comparisons" subtitle="Pre-draft measurable & production similarity — not an outcome prediction">
        {comparisons.length === 0 ? (
          <p className="text-sm text-[var(--color-text-faint)]">No comparable historical profiles found.</p>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {comparisons.map((c, i) => (
              <div key={c.player_name} className="rounded border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-3">
                <div className="text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">Match #{i + 1}</div>
                <div className="text-sm font-medium text-[var(--color-text)]">{c.player_name}</div>
                <div className="text-xs text-[var(--color-text-muted)]">{c.college ?? "—"} · {c.draft_year}</div>
                <div className="mt-1 font-mono text-lg text-[var(--color-accent)]">{c.similarity.toFixed(0)}%</div>
                <p className="mt-1 text-[11px] text-[var(--color-text-faint)]">{c.note}</p>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b border-[var(--color-border-subtle)] py-1 last:border-0">
      <dt className="capitalize text-[var(--color-text-faint)]">{label}</dt>
      <dd className="font-mono text-[var(--color-text)]">{value}</dd>
    </div>
  );
}
