import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Clock } from "lucide-react";
import { toast } from "sonner";
import { apiClient } from "../lib/api";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Switch } from "./ui/switch";
import { EditButton } from "./ui/edit-button";
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "./ui/drawer";
import type { ScheduleSettings } from "../types/api";

interface SyncScheduleDrawerProps {
  settings?: ScheduleSettings;
  trigger?: React.ReactNode;
}

export default function SyncScheduleDrawer({
  settings,
  trigger,
}: SyncScheduleDrawerProps) {
  const [open, setOpen] = useState(false);
  const [config, setConfig] = useState({
    enabled: true,
    hour: 3,
    minute: 0,
    cron: "",
    useCron: false,
  });

  const queryClient = useQueryClient();

  useEffect(() => {
    if (settings) {
      setConfig({
        enabled: settings.enabled,
        hour: settings.hour,
        minute: settings.minute,
        cron: settings.cron || "",
        useCron: !!settings.cron,
      });
    }
  }, [settings]);

  const updateMutation = useMutation({
    mutationFn: (scheduleConfig: Omit<ScheduleSettings, "next_sync_time">) =>
      apiClient.updateScheduleSettings(scheduleConfig),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scheduleSettings"] });
      setOpen(false);
      toast.success("Sync schedule updated successfully");
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message =
        error?.response?.data?.detail ||
        "Failed to update sync schedule. Please check your settings.";
      toast.error(message);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate({
      enabled: config.enabled,
      hour: config.hour,
      minute: config.minute,
      cron: config.useCron && config.cron ? config.cron : undefined,
    });
  };

  return (
    <Drawer open={open} onOpenChange={setOpen}>
      <DrawerTrigger asChild>{trigger || <EditButton />}</DrawerTrigger>
      <DrawerContent>
        <div className="mx-auto w-full max-w-sm">
          <DrawerHeader>
            <DrawerTitle className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-primary" />
              <span>Sync Schedule</span>
            </DrawerTitle>
            <DrawerDescription>
              Configure when automatic syncs run
            </DrawerDescription>
          </DrawerHeader>

          <form onSubmit={handleSubmit} className="px-4 space-y-4">
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

            <DrawerFooter className="px-0">
              <Button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending ? "Saving..." : "Save Schedule"}
              </Button>
              <DrawerClose asChild>
                <Button variant="ghost">Cancel</Button>
              </DrawerClose>
            </DrawerFooter>
          </form>
        </div>
      </DrawerContent>
    </Drawer>
  );
}
