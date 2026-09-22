import { useQuery } from "@tanstack/react-query";
import { Clock } from "lucide-react";
import { apiClient } from "../../lib/api";
import { queryKeys } from "../../lib/queryKeys";
import { formatDateTime } from "../../lib/utils";
import { CardContent } from "../ui/card";
import SettingsCard from "./SettingsCard";
import SyncScheduleDrawer from "./SyncScheduleDrawer";

export default function SyncScheduleCard() {
  const query = useQuery({
    queryKey: queryKeys.scheduleSettings,
    queryFn: apiClient.getScheduleSettings,
  });

  return (
    <SettingsCard
      icon={Clock}
      title="Sync Schedule"
      description="Configure automatic sync scheduling"
      action={<SyncScheduleDrawer settings={query.data} />}
      query={query}
    >
      {(schedule) => (
        <CardContent>
          <div className="bg-muted rounded-md p-4">
            <div className="flex items-center space-x-3 mb-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  schedule.enabled ? "bg-green-500" : "bg-muted-foreground"
                }`}
                aria-hidden="true"
              />
              <span className="text-sm font-medium">
                {schedule.enabled ? "Enabled" : "Disabled"}
              </span>
            </div>
            {schedule.enabled && (
              <div className="space-y-1 text-sm text-muted-foreground">
                <p>
                  {schedule.cron
                    ? `Custom schedule: ${schedule.cron}`
                    : `Daily at ${String(schedule.hour).padStart(2, "0")}:${String(schedule.minute).padStart(2, "0")}`}
                </p>
                {schedule.next_sync_time && (
                  <p>Next sync: {formatDateTime(schedule.next_sync_time)}</p>
                )}
              </div>
            )}
          </div>
        </CardContent>
      )}
    </SettingsCard>
  );
}
