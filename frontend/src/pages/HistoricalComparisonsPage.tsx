import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAppState } from "../context/AppContext";
import { ProspectsAPI } from "../services/api";
import type { HistoricalComparison, ProspectSummary } from "../types";
import { Card, ErrorState, Loading } from "../components/Card";
import { PositionTag } from "../components/Badges";

export function HistoricalComparisonsPage() {
  const { draftYear } = useAppState();
  const [prospects, setProspects] = useState<ProspectSummary[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [comparisons, setComparisons] = useState<HistoricalComparison[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    ProspectsAPI.list({ draft_year: draftYear, sort_by: "draft_grade", limit: 300 })
      .then((rows) => {
        setProspects(rows);
        setSelectedId(rows[0]?.id ?? null);
      })
      .catch(() => setError("Could not load prospects."))
      .finally(() => setLoading(false));
  }, [draftYear]);

  useEffect(() => {
    if (!selectedId) return;
    ProspectsAPI.comparisons(selectedId).then(setComparisons).catch(() => setComparisons([]));
  }, [selectedId]);

  if (loading) return <Loading label="Loading prospects..." />;
  if (error) return <ErrorState message={error} />;

  const selected = prospects.find((p) => p.id === selectedId);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-[var(--color-text)]">Historical Player Comparisons</h1>
        <p className="mt-1 max-w-3xl text-sm text-[var(--color-text-muted)]">
          Finds the historical (demo) players whose pre-draft measurables and college production most closely
          resemble a current prospect's, using StandardScaler-normalized features and cosine similarity within the
          same position group. These are similarity matches on pre-draft profile only — not outcome predictions.
        </p>
      </div>

      <Card>
        <label className="flex flex-col gap-1 text-xs text-[var(--color-text-faint)]">
          Select a Prospect
          <select
            value={selectedId ?? ""}
            onChange={(e) => setSelectedId(Number(e.target.value))}
            className="w-72 rounded border border-[var(--color-border)] bg-[var(--color-panel-raised)] px-2 py-1.5 text-sm text-[var(--color-text)]"
          >
            {prospects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.position}, {p.college})
              </option>
            ))}
          </select>
        </label>
      </Card>

      {selected && (
        <Card title={`Most Similar Pre-Draft Profiles to ${selected.name}`}>
          {comparisons.length === 0 ? (
            <p className="text-sm text-[var(--color-text-faint)]">No comparable historical profiles found for this position.</p>
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {comparisons.map((c, i) => (
                <div key={c.player_name} className="rounded border border-[var(--color-border)] bg-[var(--color-panel-raised)] p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">Match #{i + 1}</span>
                    <PositionTag position={c.position} />
                  </div>
                  <div className="mt-1 text-base font-medium text-[var(--color-text)]">{c.player_name}</div>
                  <div className="text-xs text-[var(--color-text-muted)]">{c.college ?? "—"} · {c.draft_year}</div>
                  <div className="mt-2 font-mono text-2xl text-[var(--color-accent)]">{c.similarity.toFixed(0)}%</div>
                  <p className="mt-2 text-[11px] text-[var(--color-text-faint)]">{c.note}</p>
                </div>
              ))}
            </div>
          )}
          <div className="mt-4">
            <Link to={`/prospects/${selected.id}`} className="text-xs text-[var(--color-accent)] hover:underline">
              View full profile →
            </Link>
          </div>
        </Card>
      )}
    </div>
  );
}
