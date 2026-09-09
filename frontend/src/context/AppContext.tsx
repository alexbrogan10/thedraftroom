import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { TeamsAPI } from "../services/api";
import type { Team } from "../types";

interface AppState {
  teams: Team[];
  teamsLoading: boolean;
  selectedTeamId: number | null;
  setSelectedTeamId: (id: number) => void;
  selectedTeam: Team | null;
  draftYear: number;
  setDraftYear: (y: number) => void;
  currentPick: number;
  setCurrentPick: (p: number) => void;
}

const AppContext = createContext<AppState | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamsLoading, setTeamsLoading] = useState(true);
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null);
  const [draftYear, setDraftYear] = useState(2026);
  const [currentPick, setCurrentPick] = useState(12);

  useEffect(() => {
    TeamsAPI.list()
      .then((data) => {
        setTeams(data);
        if (data.length > 0) {
          const cle = data.find((t) => t.abbreviation === "CLE");
          setSelectedTeamId(cle ? cle.id : data[0].id);
        }
      })
      .finally(() => setTeamsLoading(false));
  }, []);

  const selectedTeam = useMemo(
    () => teams.find((t) => t.id === selectedTeamId) ?? null,
    [teams, selectedTeamId]
  );

  const value: AppState = {
    teams,
    teamsLoading,
    selectedTeamId,
    setSelectedTeamId,
    selectedTeam,
    draftYear,
    setDraftYear,
    currentPick,
    setCurrentPick,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppState() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useAppState must be used within AppProvider");
  return ctx;
}
