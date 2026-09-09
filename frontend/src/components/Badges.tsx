function riskColor(level: string) {
  const l = level.toUpperCase();
  if (l.includes("LOW")) return "text-[var(--color-risk-low)] border-[var(--color-risk-low)]/40 bg-[var(--color-risk-low)]/10";
  if (l.includes("HIGH")) return "text-[var(--color-risk-high)] border-[var(--color-risk-high)]/40 bg-[var(--color-risk-high)]/10";
  return "text-[var(--color-risk-moderate)] border-[var(--color-risk-moderate)]/40 bg-[var(--color-risk-moderate)]/10";
}

export function RiskBadge({ level }: { level: string }) {
  return (
    <span className={`inline-flex items-center rounded border px-2 py-0.5 text-[11px] font-medium tracking-wide uppercase ${riskColor(level)}`}>
      {level.replace(" RISK", "")}
    </span>
  );
}

const VALUE_STYLES: Record<string, string> = {
  "Significant Value": "text-[var(--color-risk-low)] border-[var(--color-risk-low)]/40 bg-[var(--color-risk-low)]/10",
  "Potential Value": "text-emerald-300 border-emerald-400/30 bg-emerald-400/10",
  "Fair Value": "text-[var(--color-text-muted)] border-[var(--color-border)] bg-white/5",
  "Potential Reach": "text-orange-300 border-orange-400/30 bg-orange-400/10",
  "Significant Reach": "text-[var(--color-risk-high)] border-[var(--color-risk-high)]/40 bg-[var(--color-risk-high)]/10",
};

export function ValueBadge({ classification, icon }: { classification: string; icon: string }) {
  const style = VALUE_STYLES[classification] ?? VALUE_STYLES["Fair Value"];
  return (
    <span className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 text-[11px] font-medium ${style}`}>
      <span>{icon}</span>
      {classification}
    </span>
  );
}

export function GradePill({ value }: { value: number }) {
  let color = "text-[var(--color-text-muted)]";
  if (value >= 90) color = "text-[var(--color-accent)]";
  else if (value >= 80) color = "text-[var(--color-risk-low)]";
  else if (value >= 65) color = "text-[var(--color-risk-moderate)]";
  else color = "text-[var(--color-risk-high)]";
  return <span className={`font-mono text-base font-semibold ${color}`}>{value.toFixed(1)}</span>;
}

export function PositionTag({ position }: { position: string }) {
  return (
    <span className="inline-flex items-center rounded bg-[var(--color-panel-raised)] border border-[var(--color-border)] px-1.5 py-0.5 text-[11px] font-mono text-[var(--color-text-muted)]">
      {position}
    </span>
  );
}
