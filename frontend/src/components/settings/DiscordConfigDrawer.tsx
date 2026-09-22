import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { MessageSquare } from "lucide-react";
import { toast } from "sonner";
import { apiClient, MASKED_SECRET } from "../../lib/api";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Switch } from "../ui/switch";
import SettingsDrawer, {
  TestButton,
  useSettingsDrawer,
  useSettingsMutation,
} from "./SettingsDrawer";
import type { NotificationSettings, DiscordConfig } from "../../types/api";
import { queryKeys } from "../../lib/queryKeys";
import { getTestNotificationErrorMessage } from "../../lib/notification-errors";

const EMPTY_DISCORD_CONFIG: DiscordConfig = { webhook: "", enabled: true };

interface DiscordConfigDrawerProps {
  settings: NotificationSettings | undefined;
}

export default function DiscordConfigDrawer({
  settings,
}: DiscordConfigDrawerProps) {
  const [config, setConfig] = useState<DiscordConfig>(EMPTY_DISCORD_CONFIG);
  const drawer = useSettingsDrawer(() =>
    setConfig(settings?.discord ?? EMPTY_DISCORD_CONFIG),
  );

  const save = useSettingsMutation({
    // The API merges a partial body, so only this service is sent.
    mutationFn: (discord: DiscordConfig) =>
      apiClient.updateNotificationSettings({ discord }),
    invalidates: [
      queryKeys.notificationSettings,
      queryKeys.notificationServices,
    ],
    successMessage: "Discord configuration saved.",
    errorMessage: "Failed to update Discord configuration.",
    onSuccess: drawer.close,
  });

  const test = useMutation({
    mutationFn: () => apiClient.testNotification({ service: "discord", config }),
    onSuccess: () => {
      toast.success("Test Discord notification sent.");
    },
    onError: (error) => {
      toast.error(getTestNotificationErrorMessage(error, "Discord"));
    },
  });

  // The API masks the stored webhook; the masked value means "keep it"
  const isSavedSecret = config.webhook === MASKED_SECRET;
  const isConfigValid =
    isSavedSecret ||
    (config.webhook.trim().length > 0 &&
      config.webhook.includes("discord.com/api/webhooks"));

  return (
    <SettingsDrawer
      drawer={drawer}
      icon={MessageSquare}
      title="Discord Configuration"
      description="Configure Discord webhook notifications for transaction alerts"
      onSubmit={() => save.mutate(config)}
      isSaving={save.isPending}
      saveLabel="Save Configuration"
      noValidate
      actions={
        config.enabled &&
        isConfigValid && (
          <TestButton onClick={() => test.mutate()} isPending={test.isPending} />
        )
      }
    >
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
          onChange={(e) => setConfig({ ...config, webhook: e.target.value })}
          disabled={!config.enabled}
        />
        <p className="text-xs text-muted-foreground">
          {isSavedSecret
            ? "A webhook is saved. Leave it unchanged to keep it, or paste a new URL to replace it."
            : "Create a webhook in your Discord server settings under Integrations → Webhooks"}
        </p>
      </div>

      {/* Configuration Status */}
      {config.enabled && (
        <div className="p-3 bg-muted rounded-md">
          <div className="flex items-center space-x-2">
            <div
              className={`w-2 h-2 rounded-full ${isConfigValid ? "bg-green-500" : "bg-red-500"}`}
              aria-hidden="true"
            />
            <span className="text-sm font-medium">
              {isConfigValid ? "Configuration Valid" : "Invalid Webhook URL"}
            </span>
          </div>
          {!isConfigValid && config.webhook.trim().length > 0 && (
            <p className="text-xs text-muted-foreground mt-1">
              Please enter a valid Discord webhook URL
            </p>
          )}
        </div>
      )}
    </SettingsDrawer>
  );
}
