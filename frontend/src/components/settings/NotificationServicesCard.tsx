import { useState, type ComponentType } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, MessageSquare, Send, Trash2, type LucideIcon } from "lucide-react";
import { toast } from "sonner";
import { apiClient, getApiErrorMessage } from "../../lib/api";
import { queryKeys } from "../../lib/queryKeys";
import { useNotificationSettings } from "../../hooks/queries";
import { Button } from "../ui/button";
import { CardContent } from "../ui/card";
import { Tooltip, TooltipContent, TooltipTrigger } from "../ui/tooltip";
import ConfirmDialog from "../ConfirmDialog";
import SettingsCard from "./SettingsCard";
import DiscordConfigDrawer from "./DiscordConfigDrawer";
import TelegramConfigDrawer from "./TelegramConfigDrawer";
import type { NotificationSettings } from "../../types/api";

/** How each service the API reports is drawn and edited, by its lowercase name. */
const SERVICES: Record<
  string,
  {
    icon: LucideIcon;
    Drawer: ComponentType<{ settings: NotificationSettings | undefined }>;
  }
> = {
  discord: { icon: MessageSquare, Drawer: DiscordConfigDrawer },
  telegram: { icon: Send, Drawer: TelegramConfigDrawer },
};

export default function NotificationServicesCard() {
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: queryKeys.notificationServices,
    queryFn: apiClient.getNotificationServices,
  });
  // The drawers seed their forms from the saved settings.
  const { data: settings } = useNotificationSettings();

  const deleteService = useMutation({
    mutationFn: apiClient.deleteNotificationService,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notificationSettings });
      queryClient.invalidateQueries({ queryKey: queryKeys.notificationServices });
      setDeleteTarget(null);
      toast.success("Notification service deleted.");
    },
    onError: (error) => {
      toast.error(
        getApiErrorMessage(error, "Failed to delete notification service."),
      );
    },
  });

  return (
    <SettingsCard
      icon={Bell}
      title="Notification Services"
      description="Manage your notification services"
      query={query}
    >
      {(services) =>
        services.length === 0 ? (
          <CardContent className="text-center">
            <Bell className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              No notification services configured
            </h3>
            <p className="text-muted-foreground">
              Configure notification services in your backend to receive
              alerts.
            </p>
          </CardContent>
        ) : (
          <CardContent className="p-0">
            <div className="divide-y divide-border">
              {services.map((service) => {
                const known = SERVICES[service.name.toLowerCase()];
                const Icon = known?.icon ?? Bell;
                return (
                  <div
                    key={service.name}
                    className="p-6 hover:bg-accent transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="p-3 bg-muted rounded-full">
                          <Icon className="h-6 w-6 text-muted-foreground" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <h4 className="text-lg font-medium text-foreground capitalize">
                              {service.name}
                            </h4>
                            <div className="flex items-center space-x-2">
                              <div
                                className={`w-2 h-2 rounded-full ${
                                  service.active
                                    ? "bg-green-500"
                                    : !service.configured
                                      ? "bg-amber-500"
                                      : "bg-muted-foreground"
                                }`}
                                aria-hidden="true"
                              />
                              <span className="text-sm text-muted-foreground">
                                {/* `active` is the real on/off signal: the
                                    service is both switched on and holds
                                    credentials. Missing credentials outrank
                                    the switch in what the user must fix. */}
                                {service.active
                                  ? "Active"
                                  : !service.configured
                                    ? "Needs Configuration"
                                    : "Disabled"}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        {known && <known.Drawer settings={settings} />}

                        <Tooltip>
                          <TooltipTrigger
                            render={
                              <Button
                                onClick={() => setDeleteTarget(service.name)}
                                disabled={deleteService.isPending}
                                variant="ghost"
                                size="icon"
                                aria-label={`Delete ${service.name}`}
                                className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            }
                          />
                          <TooltipContent>Delete service</TooltipContent>
                        </Tooltip>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <ConfirmDialog
              open={!!deleteTarget}
              onClose={() => setDeleteTarget(null)}
              onConfirm={() => {
                if (deleteTarget) {
                  deleteService.mutate(deleteTarget.toLowerCase());
                }
              }}
              isPending={deleteService.isPending}
              title="Delete Notification Service"
              description={
                <>
                  Are you sure you want to delete the{" "}
                  <span className="font-medium text-foreground capitalize">
                    {deleteTarget}
                  </span>{" "}
                  notification service?
                </>
              }
              confirmLabel="Delete"
            />
          </CardContent>
        )
      }
    </SettingsCard>
  );
}
