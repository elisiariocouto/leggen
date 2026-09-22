import { useState } from "react";
import { Clock } from "lucide-react";
import { apiClient } from "../../lib/api";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Switch } from "../ui/switch";
import SettingsDrawer, {
  useSettingsDrawer,
  useSettingsMutation,
} from "./SettingsDrawer";
import type { ScheduleSettings } from "../../types/api";
import { queryKeys } from "../../lib/queryKeys";

interface SyncScheduleDrawerProps {
  settings?: ScheduleSettings;
}

export default function SyncScheduleDrawer({
  settings,
}: SyncScheduleDrawerProps) {
  const [config, setConfig] = useState({
    enabled: true,
    hour: 3,
    minute: 0,
    cron: "",
    useCron: false,
  });
  const drawer = useSettingsDrawer(() => {
    if (settings) {
      setConfig({
        enabled: settings.enabled,
        hour: settings.hour,
        minute: settings.minute,
        cron: settings.cron || "",
        useCron: !!settings.cron,
      });
    }
  });

  const save = useSettingsMutation({
    mutationFn: (scheduleConfig: Omit<ScheduleSettings, "next_sync_time">) =>
      apiClient.updateScheduleSettings(scheduleConfig),
    invalidates: [queryKeys.scheduleSettings],
    successMessage: "Sync schedule updated successfully",
    errorMessage: "Failed to update sync schedule. Please check your settings.",
    onSuccess: drawer.close,
  });

  const handleSubmit = () => {
    save.mutate({
      enabled: config.enabled,
      hour: config.hour,
      minute: config.minute,
      cron: config.useCron && config.cron ? config.cron : undefined,
    });
  };

  return (
    <SettingsDrawer
      drawer={drawer}
      icon={Clock}
      title="Sync Schedule"
      description="Configure when automatic syncs run"
      width="sm"
      onSubmit={handleSubmit}
      isSaving={save.isPending}
      saveLabel="Save Schedule"
    >
      <div className="flex items-center space-x-2">
        <Switch
          id="schedule-enabled"
          checked={config.enabled}
          onCheckedChange={(checked) =>
            setConfig({ ...config, enabled: checked })
          }
        />
        <Label htmlFor="schedule-enabled">Enable scheduled sync</Label>
      </div>

      {config.enabled && (
        <>
          <div className="flex items-center space-x-2">
            <Switch
              id="use-cron"
              checked={config.useCron}
              onCheckedChange={(checked) =>
                setConfig({ ...config, useCron: checked })
              }
            />
            <Label htmlFor="use-cron">Use custom cron expression</Label>
          </div>

          {config.useCron ? (
            <div className="space-y-2">
              <Label htmlFor="cron">Cron Expression</Label>
              <Input
                id="cron"
                type="text"
                value={config.cron}
                onChange={(e) =>
                  setConfig({ ...config, cron: e.target.value })
                }
                placeholder="0 3 * * *"
              />
              <p className="text-xs text-muted-foreground">
                Format: minute hour day month day_of_week (e.g., "0 3 * *
                *" for daily at 3:00 AM)
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="hour">Hour (0-23)</Label>
                <Input
                  id="hour"
                  type="number"
                  min={0}
                  max={23}
                  value={config.hour}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      hour: parseInt(e.target.value) || 0,
                    })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="minute">Minute (0-59)</Label>
                <Input
                  id="minute"
                  type="number"
                  min={0}
                  max={59}
                  value={config.minute}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      minute: parseInt(e.target.value) || 0,
                    })
                  }
                />
              </div>
            </div>
          )}
        </>
      )}
    </SettingsDrawer>
  );
}
