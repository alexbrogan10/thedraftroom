import { NavLink, Outlet } from "react-router-dom";
import { useAppState } from "../context/AppContext";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/big-board", label: "Big Board" },
  { to: "/explorer", label: "Prospect Explorer" },
  { to: "/hidden-values", label: "Hidden Values" },
  { to: "/risk", label: "Risk Analysis" },
  { to: "/team-fit", label: "Team Fit" },
  { to: "/simulator", label: "Draft Simulator" },
  { to: "/comparisons", label: "Historical Comparisons" },
  { to: "/methodology", label: "Data & Model" },
];

export function Layout() {
  const { teams, selectedTeamId, setSelectedTeamId, draftYear, setDraftYear, currentPick, setCurrentPick } =
    useAppState();

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-60 shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-panel)]">
        <div className="border-b border-[var(--color-border-subtle)] px-5 py-5">
          <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--color-accent)]">
            The Draft Room
          </div>
          <div className="mt-0.5 text-[11px] text-[var(--color-text-faint)]">Data-Driven NFL Draft Intelligence</div>
        </div>
        <nav className="flex-1 space-y-0.5 px-2 py-3">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `block rounded px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-[var(--color-panel-raised)] text-[var(--color-text)] border-l-2 border-[var(--color-accent)]"
                    : "text-[var(--color-text-muted)] hover:bg-[var(--color-panel-raised)] hover:text-[var(--color-text)]"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-[var(--color-border-subtle)] px-4 py-3 text-[10px] leading-relaxed text-[var(--color-text-faint)]">
          Independent portfolio project. Not affiliated with the NFL. All demo data is synthetic.
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-panel)] px-6 py-3">
          <div className="flex items-center gap-6">
            <div className="flex flex-col">
              <label className="text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">Team</label>
              <select
                className="mt-0.5 rounded border border-[var(--color-border)] bg-[var(--color-panel-raised)] px-2 py-1 text-sm text-[var(--color-text)] focus:border-[var(--color-accent)] focus:outline-none"
                value={selectedTeamId ?? ""}
                onChange={(e) => setSelectedTeamId(Number(e.target.value))}
              >
                {teams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col">
              <label className="text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">Draft Class</label>
              <select
                className="mt-0.5 rounded border border-[var(--color-border)] bg-[var(--color-panel-raised)] px-2 py-1 text-sm text-[var(--color-text)] focus:border-[var(--color-accent)] focus:outline-none"
                value={draftYear}
                onChange={(e) => setDraftYear(Number(e.target.value))}
              >
                <option value={2026}>2026</option>
              </select>
            </div>
            <div className="flex flex-col">
              <label className="text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">Current Pick</label>
              <input
                type="number"
                min={1}
                max={262}
                value={currentPick}
                onChange={(e) => setCurrentPick(Number(e.target.value))}
                className="mt-0.5 w-20 rounded border border-[var(--color-border)] bg-[var(--color-panel-raised)] px-2 py-1 text-sm text-[var(--color-text)] focus:border-[var(--color-accent)] focus:outline-none"
              />
            </div>
          </div>
          <div className="text-right text-[11px] text-[var(--color-text-faint)]">
            Demo dataset · synthetic prospects &amp; rosters
          </div>
        </header>
        <main className="field-texture flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
