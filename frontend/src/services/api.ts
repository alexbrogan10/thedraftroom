import axios from "axios";
import type {
  BoardEntry,
  ModelPerformance,
  OutcomePrediction,
  ProspectAnalytics,
  ProspectDetail,
  ProspectSummary,
  RecommendResponse,
  SimulateResponse,
  Team,
  TeamFit,
  TeamNeed,
  TradeAnalysisResponse,
  HistoricalComparison,
  RiskProfile,
} from "../types";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({ baseURL });

export interface ProspectListParams {
  draft_year?: number;
  position?: string;
  college?: string;
  min_age?: number;
  max_age?: number;
  min_draft_grade?: number;
  max_risk?: number;
  projected_round?: number;
  sort_by?: "draft_grade" | "team_fit" | "value_score" | "risk_score" | "projected_pick";
  descending?: boolean;
  limit?: number;
}

export const ProspectsAPI = {
  list: (params: ProspectListParams = {}) =>
    api.get<ProspectSummary[]>("/api/prospects", { params }).then((r) => r.data),
  get: (id: number) => api.get<ProspectDetail>(`/api/prospects/${id}`).then((r) => r.data),
  analytics: (id: number) =>
    api.get<ProspectAnalytics>(`/api/prospects/${id}/analytics`).then((r) => r.data),
  risk: (id: number) => api.get<RiskProfile>(`/api/prospects/${id}/risk`).then((r) => r.data),
  teamFit: (id: number, teamId: number) =>
    api
      .get<TeamFit>(`/api/prospects/${id}/team-fit`, { params: { team_id: teamId } })
      .then((r) => r.data),
  comparisons: (id: number) =>
    api.get<HistoricalComparison[]>(`/api/prospects/${id}/comparisons`).then((r) => r.data),
  outcomePrediction: (id: number) =>
    api.get<OutcomePrediction>(`/api/prospects/${id}/outcome-prediction`).then((r) => r.data),
};

export const ModelAPI = {
  performance: () => api.get<ModelPerformance>("/api/model/performance").then((r) => r.data),
};

export const TeamsAPI = {
  list: () => api.get<Team[]>("/api/teams").then((r) => r.data),
  needs: (teamId: number, season?: number) =>
    api
      .get<TeamNeed[]>(`/api/teams/${teamId}/needs`, { params: { season } })
      .then((r) => r.data),
  draftBoard: (teamId: number, draftYear: number, limit = 100) =>
    api
      .get<BoardEntry[]>(`/api/teams/${teamId}/draft-board`, {
        params: { draft_year: draftYear, limit },
      })
      .then((r) => r.data),
};

export const DraftAPI = {
  board: (draftYear: number, limit = 200) =>
    api.get<BoardEntry[]>("/api/draft/board", { params: { draft_year: draftYear, limit } }).then((r) => r.data),
  recommend: (payload: { team_id: number; draft_year: number; pick_number: number; excluded_prospect_ids: number[] }) =>
    api.post<RecommendResponse>("/api/draft/recommend", payload).then((r) => r.data),
  simulate: (payload: { team_id: number; draft_year: number; pick_number: number; drafted_prospect_ids: number[] }) =>
    api.post<SimulateResponse>("/api/draft/simulate", payload).then((r) => r.data),
  tradeAnalysis: (payload: { draft_year: number; current_pick: number; target_prospect_id: number; alternative_picks: number[] }) =>
    api.post<TradeAnalysisResponse>("/api/draft/trade-analysis", payload).then((r) => r.data),
};
