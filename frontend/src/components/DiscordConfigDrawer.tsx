import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { MessageSquare, TestTube } from "lucide-react";
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
import type { NotificationSettings, DiscordConfig } from "../types/api";

interface DiscordConfigDrawerProps {
  settings: NotificationSettings | undefined;
  trigger?: React.ReactNode;
}

export default function DiscordConfigDrawer({
  settings,
  trigger,
}: DiscordConfigDrawerProps) {
  const [open, setOpen] = useState(false);
  const [config, setConfig] = useState<DiscordConfig>({
    webhook: "",
    enabled: true,
  });

  const queryClient = useQueryClient();

  useEffect(() => {
    if (settings?.discord) {
      setConfig({ ...settings.discord });
    }
  }, [settings]);

  const updateMutation = useMutation({
    mutationFn: (discordConfig: DiscordConfig) =>
      apiClient.updateNotificationSettings({
        ...settings,
        discord: discordConfig,
        filters: settings?.filters || {
          case_insensitive: [],
          case_sensitive: [],
        },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notificationSettings"] });
      queryClient.invalidateQueries({ queryKey: ["notificationServices"] });
      setOpen(false);
    },
    onError: (error) => {
      console.error("Failed to update Discord configuration:", error);
    },
  });

  const testMutation = useMutation({
    mutationFn: () =>
      apiClient.testNotification({
        service: "discord",
        message:
          "Test notification from Leggen - Discord configuration is working!",
      }),
    onSuccess: () => {
      console.log("Test Discord notification sent successfully");
    },
    onError: (error) => {
      console.error("Failed to send test Discord notification:", error);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate(config);
  };

  const handleTest = () => {
    testMutation.mutate();
  };

  const isConfigValid =
    config.webhook.trim().length > 0 &&
    config.webhook.includes("discord.com/api/webhooks");

  return (
    <Drawer open={open} onOpenChange={setOpen}>
      <DrawerTrigger asChild>{trigger || <EditButton />}</DrawerTrigger>
      <DrawerContent>
        <div className="mx-auto w-full max-w-md">
          <DrawerHeader>
            <DrawerTitle className="flex items-center space-x-2">
              <MessageSquare className="h-5 w-5 text-primary" />
              <span>Discord Configuration</span>
            </DrawerTitle>
            <DrawerDescription>
              Configure Discord webhook notifications for transaction alerts
            </DrawerDescription>
          </DrawerHeader>

          <form onSubmit={handleSubmit} className="p-4 space-y-6">
            {/* Enable/Disable Toggle */}
            <div className="flex items-center justify-between">
              <Label className="text-base font-medium">
                Enable Discord Notifications
              </Label>
              <Switch
                checked={config.enabled}
                onCheckedChange={(enabled) => setConfig({ ...config, enabled })}
              />
            </div>

            {/* Webhook URL */}
            <div className="space-y-2">
              <Label htmlFor="discord-webhook">Discord Webhook URL</Label>
              <Input
                id="discord-webhook"
                type="url"
                placeholder="https://discord.com/api/webhooks/..."
                value={config.webhook}
                onChange={(e) =>
                  setConfig({ ...config, webhook: e.target.value })
                }
                disabled={!config.enabled}
              />
              <p className="text-xs text-muted-foreground">
                Create a webhook in your Discord server settings under
                Integrations → Webhooks
              </p>
            </div>

            {/* Configuration Status */}
            {config.enabled && (
              <div className="p-3 bg-muted rounded-md">
                <div className="flex items-center space-x-2">
                  <div
                    className={`w-2 h-2 rounded-full ${isConfigValid ? "bg-green-500" : "bg-red-500"}`}
                  />
                  <span className="text-sm font-medium">
                    {isConfigValid
                      ? "Configuration Valid"
                      : "Invalid Webhook URL"}
                  </span>
                </div>
                {!isConfigValid && config.webhook.trim().length > 0 && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Please enter a valid Discord webhook URL
                  </p>
                )}
              </div>
            )}

            <DrawerFooter className="px-0">
              <div className="flex space-x-2">
                <Button
                  type="submit"
                  disabled={updateMutation.isPending || !config.enabled}
                >
                  {updateMutation.isPending
                    ? "Saving..."
                    : "Save Configuration"}
                </Button>
                {config.enabled && isConfigValid && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleTest}
                    disabled={testMutation.isPending}
                  >
                    {testMutation.isPending ? (
                      <>
                        <TestTube className="h-4 w-4 mr-2 animate-spin" />
                        Testing...
                      </>
                    ) : (
                      <>
                        <TestTube className="h-4 w-4 mr-2" />
                        Test
                      </>
                    )}
                  </Button>
                )}
              </div>
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
