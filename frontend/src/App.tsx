import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { BigBoard } from "./pages/BigBoard";
import { ProspectExplorer } from "./pages/ProspectExplorer";
import { ProspectProfile } from "./pages/ProspectProfile";
import { HiddenValues } from "./pages/HiddenValues";
import { RiskAnalysis } from "./pages/RiskAnalysis";
import { TeamFitPage } from "./pages/TeamFitPage";
import { DraftSimulator } from "./pages/DraftSimulator";
import { HistoricalComparisonsPage } from "./pages/HistoricalComparisonsPage";
import { Methodology } from "./pages/Methodology";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="big-board" element={<BigBoard />} />
        <Route path="explorer" element={<ProspectExplorer />} />
        <Route path="prospects/:id" element={<ProspectProfile />} />
        <Route path="hidden-values" element={<HiddenValues />} />
        <Route path="risk" element={<RiskAnalysis />} />
        <Route path="team-fit" element={<TeamFitPage />} />
        <Route path="simulator" element={<DraftSimulator />} />
        <Route path="comparisons" element={<HistoricalComparisonsPage />} />
        <Route path="methodology" element={<Methodology />} />
      </Route>
    </Routes>
  );
}
