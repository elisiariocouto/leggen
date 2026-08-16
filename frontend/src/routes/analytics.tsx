import { createFileRoute } from "@tanstack/react-router";
import { lazy, Suspense } from "react";
import { Skeleton } from "../components/ui/skeleton";

// Recharts is ~415 kB — by far the largest dependency, and analytics is the
// only route that draws charts. Loading it here keeps it off the critical
// path for the transactions, accounts, sync, settings and login pages.
const AnalyticsDashboard = lazy(
  () => import("../components/analytics/AnalyticsDashboard"),
);

function AnalyticsFallback() {
  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Skeleton className="h-9 w-[260px]" />
        <Skeleton className="h-9 w-[220px]" />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Skeleton className="h-96" />
        <Skeleton className="h-96" />
      </div>
    </div>
  );
}

export const Route = createFileRoute("/analytics")({
  component: () => (
    <Suspense fallback={<AnalyticsFallback />}>
      <AnalyticsDashboard />
    </Suspense>
  ),
});
