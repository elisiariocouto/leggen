import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Send, TestTube } from "lucide-react";
import { toast } from "sonner";
import { apiClient, getApiErrorMessage, MASKED_SECRET } from "../lib/api";
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
import type { NotificationSettings, TelegramConfig } from "../types/api";
import { queryKeys } from "../lib/queryKeys";

interface TelegramConfigDrawerProps {
  settings: NotificationSettings | undefined;
}

export default function TelegramConfigDrawer({
  settings,
}: TelegramConfigDrawerProps) {
  const [open, setOpen] = useState(false);
  const [config, setConfig] = useState<TelegramConfig>({
    token: "",
    chat_id: 0,
    enabled: true,
  });

  const queryClient = useQueryClient();

  // Seed on open rather than mirroring props into state (see Discord).
  const handleOpenChange = (next: boolean) => {
    if (next) {
      setConfig(settings?.telegram ?? { token: "", chat_id: 0, enabled: true });
    }
    setOpen(next);
  };

  const updateMutation = useMutation({
    mutationFn: (telegramConfig: TelegramConfig) =>
      apiClient.updateNotificationSettings({
        ...settings,
        telegram: telegramConfig,
        filters: settings?.filters || {
          case_insensitive: [],
          case_sensitive: [],
        },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notificationSettings });
      queryClient.invalidateQueries({ queryKey: queryKeys.notificationServices });
      setOpen(false);
      toast.success("Telegram configuration saved.");
    },
    onError: (error) => {
      toast.error(
        getApiErrorMessage(error, "Failed to update Telegram configuration."),
      );
    },
  });

  const testMutation = useMutation({
    mutationFn: () => apiClient.testNotification({ service: "telegram" }),
    onSuccess: () => {
      toast.success("Test Telegram notification sent.");
    },
    onError: (error) => {
      toast.error(
        getApiErrorMessage(
          error,
          "Failed to send test Telegram notification.",
        ),
      );
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate(config);
  };

  const handleTest = () => {
    testMutation.mutate();
  };

  // The API masks the stored token; the masked value means "keep it"
  const isSavedSecret = config.token === MASKED_SECRET;
  const isConfigValid = config.token.trim().length > 0 && config.chat_id !== 0;

  return (
    <Drawer open={open} onOpenChange={handleOpenChange}>
      <DrawerTrigger asChild><EditButton /></DrawerTrigger>
      <DrawerContent>
        <div className="mx-auto w-full max-w-md">
          <DrawerHeader>
            <DrawerTitle className="flex items-center space-x-2">
              <Send className="h-5 w-5 text-primary" />
              <span>Telegram Configuration</span>
            </DrawerTitle>
            <DrawerDescription>
              Configure Telegram bot notifications for transaction alerts
            </DrawerDescription>
          </DrawerHeader>

          <form onSubmit={handleSubmit} className="p-4 space-y-6">
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
                onChange={(e) =>
                  setConfig({ ...config, token: e.target.value })
                }
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
                https://api.telegram.org/bot&lt;token&gt;/getUpdates to find
                your chat ID
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
                    {isConfigValid
                      ? "Configuration Valid"
                      : "Missing Token or Chat ID"}
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

            <DrawerFooter className="px-0">
              <div className="flex space-x-2">
                <Button
                  type="submit"
                  disabled={updateMutation.isPending}
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
