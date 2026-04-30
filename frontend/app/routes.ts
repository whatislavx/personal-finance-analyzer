import { createBrowserRouter } from "react-router";
import { Landing } from "./pages/Landing";
import { Dashboard } from "./pages/Dashboard";
import { Jobs } from "./pages/Jobs";
import { Results } from "./pages/Results";
import { Layout } from "./components/Layout";
import { Profile } from "./pages/Profile";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Landing,
  },
  {
    path: "/app",
    Component: Layout,
    children: [
      { index: true, Component: Dashboard },
      { path: "analyses", Component: Jobs },
      { path: "profile", Component: Profile },
      { path: "results/:analysisId", Component: Results },
    ],
  },
]);
