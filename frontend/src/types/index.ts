export interface Team {
  id: number;
  name: string;
  abbreviation: string;
  conference: string;
  division: string;
}

export interface TeamNeed {
  position: string;
  season: number;
  need_score: number;
}

export interface ProspectSummary {
  id: number;
  name: string;
  position: string;
  college: string;
  age: number | null;
  class_year: string | null;
  draft_year: number;
  draft_grade: number;
  team_fit: number | null;
  value_score: number;
  risk_score: number;
  risk_level: string;
  confidence: number;
  projected_pick: number | null;
}

export interface CombineResult {
  forty_yard_dash: number | null;
  vertical_jump: number | null;
  broad_jump: number | null;
  bench_press: number | null;
  three_cone: number | null;
  shuttle: number | null;
}

export interface ProspectStatistic {
  season: number;
  metric_name: string;
  metric_value: number;
}

export interface DraftProjection {
  source: string;
  projected_pick: number | null;
  projected_round: number | null;
}

export interface ProspectDetail {
  id: number;
  name: string;
  position: string;
  college: string;
  age: number | null;
  height_inches: number | null;
  weight_lbs: number | null;
  class_year: string | null;
  draft_year: number;
  combine: CombineResult | null;
  statistics: ProspectStatistic[];
  projections: DraftProjection[];
}

export interface ScoreBreakdown {
  score: number;
  components: Record<string, number>;
  notes: Record<string, string>;
}

export interface RiskFactor {
  score: number;
  level: string;
}

export interface RiskProfile {
  overall_risk: number;
  risk_level: string;
  factors: Record<string, RiskFactor>;
}

export interface ValueAssessment {
  analytical_rank: number;
  expected_rank: number | null;
  differential: number | null;
  value_score: number;
  classification: string;
  icon: string;
  explanation: string;
}

export interface ProspectAnalytics {
  prospect_id: number;
  draft_grade: ScoreBreakdown;
  risk: RiskProfile;
  value: ValueAssessment;
}

export interface TeamFit {
  team_id: number;
  team_abbreviation: string;
  score: number;
  components: Record<string, number>;
  explanations: Record<string, string>;
}

export interface HistoricalComparison {
  player_name: string;
  position: string;
  college: string | null;
  draft_year: number;
  similarity: number;
  note: string;
}

export interface BoardEntry {
  prospect_id: number;
  name: string;
  position: string;
  college: string;
  league_rank: number;
  team_rank: number | null;
  draft_grade: number;
  team_fit: number | null;
  value_score: number;
  value_classification: string;
  value_icon: string;
  expected_rank: number | null;
  risk_score: number;
  risk_level: string;
  reason: string | null;
}

export interface RecommendedProspect {
  prospect_id: number;
  name: string;
  position: string;
  draft_grade: number;
  team_fit: number;
  value_score: number;
  risk_score: number;
  is_primary: boolean;
}

export interface RecommendResponse {
  pick_number: number;
  recommended: RecommendedProspect;
  alternatives: RecommendedProspect[];
  reasoning: string;
}

export interface SimulatePick {
  prospect_id: number;
  name: string;
  position: string;
  draft_grade: number;
  team_fit: number;
  value_score: number;
  risk_score: number;
}

export interface SimulateResponse {
  pick_number: number;
  team_needs_snapshot: string[];
  best_available: SimulatePick[];
  remaining_prospect_count: number;
}

export interface TradeOption {
  label: string;
  pick_number: number;
  picks_moved: number;
  probability_target_available: number;
  cost_value_points: number;
  cost_description: string;
}

export interface TradeAnalysisResponse {
  target_prospect_id: number;
  target_name: string;
  current_pick_option: TradeOption;
  trade_up_options: TradeOption[];
}

export interface OutcomePrediction {
  available: boolean;
  probabilities: Record<string, number> | null;
  message?: string;
  note?: string;
}

export interface ModelLabelMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  roc_auc: number | null;
  n_train: number;
  n_test: number;
  positive_rate: number;
}

export interface ModelPerformance {
  available: boolean;
  message?: string;
  trained_at?: string;
  n_samples?: number;
  feature_columns?: string[];
  disclaimer?: string;
  labels?: Record<string, ModelLabelMetrics>;
}
