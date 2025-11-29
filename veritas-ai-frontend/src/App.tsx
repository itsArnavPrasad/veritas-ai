import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { LandingPage } from "./pages/LandingPage";
import { PipelineScreen } from "./pages/PipelineScreen";
import { ResultsPage } from "./pages/ResultsPage";
import { ErrorBoundary } from "./components/ErrorBoundary";

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/pipeline" element={<PipelineScreen />} />
          <Route path="/results/:verificationId" element={<ResultsPage />} />
        </Routes>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
