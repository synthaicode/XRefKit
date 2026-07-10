import { loadDashboardData } from "../lib/dashboard-data";
import { Dashboard } from "./skill-run-dashboard";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const result = await loadDashboardData();
  return <Dashboard initialResult={result} />;
}
