import { lazy, Suspense, useEffect } from "react";
import { BrowserRouter, Route, Routes } from "react-router";
import Navbar from "./components/Navbar";
import { getProfile } from "./lib/agent";
import Chat from "./pages/Chat";
import Landing from "./pages/Landing";
import Playground from "./pages/Playground";
import Vision from "./pages/onboarding/Vision";
import Blockers from "./pages/onboarding/Blockers";
import Ground from "./pages/onboarding/Ground";
import Commitment from "./pages/onboarding/Commitment";
import { useOnboarding } from "./store/onboarding";

const Swarm = lazy(() => import("./pages/Swarm"));
const Reveal = lazy(() => import("./pages/Reveal"));
const Opportunities = lazy(() => import("./pages/Opportunities"));
const OpportunityDetail = lazy(() => import("./pages/OpportunityDetail"));

export default function App() {
  const hydrate = useOnboarding((state) => state.hydrate);

  useEffect(() => {
    let cancelled = false;

    getProfile()
      .then((profile) => {
        if (!cancelled) {
          hydrate(profile);
        }
      })
      .catch(() => {
        // frontend should still work without the backend running
      });

    return () => {
      cancelled = true;
    };
  }, [hydrate]);

  return (
    <BrowserRouter>
      <Navbar />
      <Suspense fallback={null}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/onboarding/vision" element={<Vision />} />
          <Route path="/onboarding/blockers" element={<Blockers />} />
          <Route path="/onboarding/ground" element={<Ground />} />
          <Route path="/onboarding/commitment" element={<Commitment />} />
          <Route path="/swarm" element={<Swarm />} />
          <Route path="/reveal" element={<Reveal />} />
          <Route path="/opportunities" element={<Opportunities />} />
          <Route path="/opportunity/:id" element={<OpportunityDetail />} />
          <Route path="/playground" element={<Playground />} />
          <Route path="/debug/chat" element={<Chat />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
