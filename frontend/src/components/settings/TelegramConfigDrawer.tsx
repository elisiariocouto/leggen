import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Send } from "lucide-react";
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
import type { NotificationSettings, TelegramConfig } from "../../types/api";
import { queryKeys } from "../../lib/queryKeys";
import { getTestNotificationErrorMessage } from "../../lib/notification-errors";

const EMPTY_TELEGRAM_CONFIG: TelegramConfig = {
  token: "",
  chat_id: 0,
  enabled: true,
};

interface TelegramConfigDrawerProps {
  settings: NotificationSettings | undefined;
}

export default function TelegramConfigDrawer({
  settings,
}: TelegramConfigDrawerProps) {
  const [config, setConfig] = useState<TelegramConfig>(EMPTY_TELEGRAM_CONFIG);
  const drawer = useSettingsDrawer(() =>
    setConfig(settings?.telegram ?? EMPTY_TELEGRAM_CONFIG),
  );

  const save = useSettingsMutation({
    // The API merges a partial body, so only this service is sent.
    mutationFn: (telegram: TelegramConfig) =>
      apiClient.updateNotificationSettings({ telegram }),
    invalidates: [
      queryKeys.notificationSettings,
      queryKeys.notificationServices,
    ],
    successMessage: "Telegram configuration saved.",
    errorMessage: "Failed to update Telegram configuration.",
    onSuccess: drawer.close,
  });

  const test = useMutation({
    mutationFn: () => apiClient.testNotification({ service: "telegram", config }),
    onSuccess: () => {
      toast.success("Test Telegram notification sent.");
    },
    onError: (error) => {
      toast.error(getTestNotificationErrorMessage(error, "Telegram"));
    },
  });

  // The API masks the stored token; the masked value means "keep it"
  const isSavedSecret = config.token === MASKED_SECRET;
  const isConfigValid = config.token.trim().length > 0 && config.chat_id !== 0;

  return (
    <SettingsDrawer
      drawer={drawer}
      icon={Send}
      title="Telegram Configuration"
      description="Configure Telegram bot notifications for transaction alerts"
      onSubmit={() => save.mutate(config)}
      isSaving={save.isPending}
      saveLabel="Save Configuration"
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
          Enable Telegram Notifications
        </Label>
        <Switch
          checked={config.enabled}
          onCheckedChange={(enabled) => setConfig({ ...config, enabled })}
        />
      </div>

      {/* Bot Token */}
      <div className="space-y-2">
        <Label htmlFor="telegram-token">Bot Token</Label>
        <Input
          id="telegram-token"
          type="password"
          placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
          value={config.token}
          onChange={(e) => setConfig({ ...config, token: e.target.value })}
          disabled={!config.enabled}
        />
        <p className="text-xs text-muted-foreground">
          {isSavedSecret
            ? "A token is saved. Leave it unchanged to keep it, or enter a new token to replace it."
            : "Create a bot using @BotFather on Telegram to get your token"}
        </p>
      </div>

      {/* Chat ID */}
      <div className="space-y-2">
        <Label htmlFor="telegram-chat-id">Chat ID</Label>
        <Input
          id="telegram-chat-id"
          type="number"
          placeholder="123456789"
          value={config.chat_id || ""}
          onChange={(e) =>
            setConfig({
              ...config,
              chat_id: parseInt(e.target.value) || 0,
            })
          }
          disabled={!config.enabled}
        />
        <p className="text-xs text-muted-foreground">
          Send a message to your bot and visit
          https://api.telegram.org/bot&lt;token&gt;/getUpdates to find your chat
          ID
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
              {isConfigValid ? "Configuration Valid" : "Missing Token or Chat ID"}
            </span>
          </div>
          {!isConfigValid &&
            (config.token.trim().length > 0 || config.chat_id !== 0) && (
              <p className="text-xs text-muted-foreground mt-1">
                Both bot token and chat ID are required
              </p>
            )}
        </div>
      )}
    </SettingsDrawer>
  );
}
