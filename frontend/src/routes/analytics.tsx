import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/analytics")({
  component: () => (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Analytics</h3>
      <p className="text-gray-600">Analytics dashboard coming soon...</p>
    </div>
  ),
});
