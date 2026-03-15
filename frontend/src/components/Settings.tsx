import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  RefreshCw,
  AlertCircle,
  X,
  Bell,
  MessageSquare,
  Send,
  Trash2,
  Filter,
  Cloud,
  Archive,
  Eye,
  Clock,
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "./ui/tooltip";
import { toast } from "sonner";
import { apiClient } from "../lib/api";
import { formatDate } from "../lib/utils";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Button } from "./ui/button";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";
import { Label } from "./ui/label";

import AccountsSkeleton from "./AccountsSkeleton";
import CategoryManager from "./CategoryManager";
import NotificationFiltersDrawer from "./NotificationFiltersDrawer";
import DiscordConfigDrawer from "./DiscordConfigDrawer";
import TelegramConfigDrawer from "./TelegramConfigDrawer";
import S3BackupConfigDrawer from "./S3BackupConfigDrawer";
import SyncScheduleDrawer from "./SyncScheduleDrawer";
import type {
  NotificationSettings,
  NotificationService,
  BackupSettings,
  BackupInfo,
  ScheduleSettings,
} from "../types/api";

export default function Settings() {
  const [showBackups, setShowBackups] = useState(false);

  const queryClient = useQueryClient();

  // Notification queries
  const {
    data: notificationSettings,
    isLoading: settingsLoading,
    error: settingsError,
    refetch: refetchSettings,
  } = useQuery<NotificationSettings>({
    queryKey: ["notificationSettings"],
    queryFn: apiClient.getNotificationSettings,
  });

  const {
    data: services,
    isLoading: servicesLoading,
    error: servicesError,
    refetch: refetchServices,
  } = useQuery<NotificationService[]>({
    queryKey: ["notificationServices"],
    queryFn: apiClient.getNotificationServices,
  });

  // Schedule query
  const {
    data: scheduleSettings,
    isLoading: scheduleLoading,
    error: scheduleError,
    refetch: refetchSchedule,
  } = useQuery<ScheduleSettings>({
    queryKey: ["scheduleSettings"],
    queryFn: apiClient.getScheduleSettings,
  });

  // Backup queries
  const {
    data: backupSettings,
    isLoading: backupLoading,
    error: backupError,
    refetch: refetchBackup,
  } = useQuery<BackupSettings>({
    queryKey: ["backupSettings"],
    queryFn: apiClient.getBackupSettings,
  });

  const {
    data: backups,
    isLoading: backupsLoading,
    error: backupsError,
    refetch: refetchBackups,
  } = useQuery<BackupInfo[]>({
    queryKey: ["backups"],
    queryFn: apiClient.listBackups,
    enabled: showBackups,
  });

  // Notification mutations
  const deleteServiceMutation = useMutation({
    mutationFn: apiClient.deleteNotificationService,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notificationSettings"] });
      queryClient.invalidateQueries({ queryKey: ["notificationServices"] });
    },
    onError: () => {
      toast.error("Failed to delete notification service.");
    },
  });

  // Backup mutations
  const createBackupMutation = useMutation({
    mutationFn: () => apiClient.performBackupOperation({ operation: "backup" }),
    onSuccess: (response) => {
      if (response.success) {
        toast.success(response.message || "Backup created successfully!");
        queryClient.invalidateQueries({ queryKey: ["backups"] });
      } else {
        toast.error(response.message || "Failed to create backup.");
      }
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message =
        error?.response?.data?.detail ||
        "Failed to create backup. Please check your S3 configuration.";
      toast.error(message);
    },
  });

  // Notification handlers
  const handleDeleteService = (serviceName: string) => {
    if (
      confirm(
        `Are you sure you want to delete the ${serviceName} notification service?`,
      )
    ) {
      deleteServiceMutation.mutate(serviceName.toLowerCase());
    }
  };

  // Backup handlers
  const handleCreateBackup = () => {
    if (!backupSettings?.s3?.enabled) {
      toast.error("S3 backup is not enabled. Please configure and enable S3 backup first.");
      return;
    }
    createBackupMutation.mutate();
  };

  const handleViewBackups = () => {
    if (!backupSettings?.s3?.enabled) {
      toast.error("S3 backup is not enabled. Please configure and enable S3 backup first.");
      return;
    }
    setShowBackups(true);
  };

  const isLoading = settingsLoading || servicesLoading || backupLoading || scheduleLoading;
  const hasError = settingsError || servicesError || backupError || scheduleError;

  if (isLoading) {
    return <AccountsSkeleton />;
  }

  if (hasError) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Failed to load settings</AlertTitle>
        <AlertDescription className="space-y-3">
          <p>
            Unable to connect to the Leggen API. Please check your configuration
            and ensure the API server is running.
          </p>
          <Button
            onClick={() => {
              refetchSettings();
              refetchServices();
              refetchBackup();
              refetchSchedule();
            }}
            variant="outline"
            size="sm"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
          {/* Sync Schedule */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center space-x-2">
                  <Clock className="h-5 w-5 text-primary" />
                  <span>Sync Schedule</span>
                </CardTitle>
                <SyncScheduleDrawer settings={scheduleSettings} />
              </div>
              <CardDescription>
                Configure automatic sync scheduling
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="bg-muted rounded-md p-4">
                <div className="flex items-center space-x-3 mb-2">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      scheduleSettings?.enabled
                        ? "bg-green-500"
                        : "bg-muted-foreground"
                    }`}
                  />
                  <span className="text-sm font-medium">
                    {scheduleSettings?.enabled ? "Enabled" : "Disabled"}
                  </span>
                </div>
                {scheduleSettings?.enabled && (
                  <div className="space-y-1 text-sm text-muted-foreground">
                    <p>
                      {scheduleSettings.cron
                        ? `Custom schedule: ${scheduleSettings.cron}`
                        : `Daily at ${String(scheduleSettings.hour).padStart(2, "0")}:${String(scheduleSettings.minute).padStart(2, "0")}`}
                    </p>
                    {scheduleSettings.next_sync_time && (
                      <p>
                        Next sync: {formatDate(scheduleSettings.next_sync_time)}
                      </p>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Category Management */}
          <CategoryManager />

          {/* Notification Services */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Bell className="h-5 w-5 text-primary" />
                <span>Notification Services</span>
              </CardTitle>
              <CardDescription>
                Manage your notification services
              </CardDescription>
            </CardHeader>

            {!services || services.length === 0 ? (
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
                  {services.map((service) => (
                    <div
                      key={service.name}
                      className="p-6 hover:bg-accent transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className="p-3 bg-muted rounded-full">
                            {service.name.toLowerCase().includes("discord") ? (
                              <MessageSquare className="h-6 w-6 text-muted-foreground" />
                            ) : service.name
                                .toLowerCase()
                                .includes("telegram") ? (
                              <Send className="h-6 w-6 text-muted-foreground" />
                            ) : (
                              <Bell className="h-6 w-6 text-muted-foreground" />
                            )}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center space-x-3">
                              <h4 className="text-lg font-medium text-foreground capitalize">
                                {service.name}
                              </h4>
                              <div className="flex items-center space-x-2">
                                <div
                                  className={`w-2 h-2 rounded-full ${
                                    service.enabled && service.configured
                                      ? "bg-green-500"
                                      : service.enabled
                                        ? "bg-amber-500"
                                        : "bg-muted-foreground"
                                  }`}
                                />
                                <span className="text-sm text-muted-foreground">
                                  {service.enabled && service.configured
                                    ? "Active"
                                    : service.enabled
                                      ? "Needs Configuration"
                                      : "Disabled"}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center space-x-2">
                          {service.name.toLowerCase().includes("discord") ? (
                            <DiscordConfigDrawer
                              settings={notificationSettings}
                            />
                          ) : service.name
                              .toLowerCase()
                              .includes("telegram") ? (
                            <TelegramConfigDrawer
                              settings={notificationSettings}
                            />
                          ) : null}

                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                onClick={() => handleDeleteService(service.name)}
                                disabled={deleteServiceMutation.isPending}
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>Delete service</TooltipContent>
                          </Tooltip>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            )}
          </Card>

          {/* Notification Filters */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center space-x-2">
                  <Filter className="h-5 w-5 text-primary" />
                  <span>Notification Filters</span>
                </CardTitle>
                <NotificationFiltersDrawer settings={notificationSettings} />
              </div>
            </CardHeader>
            <CardContent>
              {notificationSettings?.filters ? (
                <div className="space-y-4">
                  <div className="bg-muted rounded-md p-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <Label className="text-xs font-medium text-muted-foreground mb-2 block">
                          Case Insensitive Filters
                        </Label>
                        <div className="min-h-[2rem] flex flex-wrap gap-1">
                          {notificationSettings.filters.case_insensitive
                            .length > 0 ? (
                            notificationSettings.filters.case_insensitive.map(
                              (filter) => (
                                <span
                                  key={filter}
                                  className="inline-flex items-center px-2 py-1 bg-secondary text-secondary-foreground rounded text-xs"
                                >
                                  {filter}
                                </span>
                              ),
                            )
                          ) : (
                            <p className="text-sm text-muted-foreground">
                              None
                            </p>
                          )}
                        </div>
                      </div>
                      <div>
                        <Label className="text-xs font-medium text-muted-foreground mb-2 block">
                          Case Sensitive Filters
                        </Label>
                        <div className="min-h-[2rem] flex flex-wrap gap-1">
                          {notificationSettings.filters.case_sensitive &&
                          notificationSettings.filters.case_sensitive.length >
                            0 ? (
                            notificationSettings.filters.case_sensitive.map(
                              (filter) => (
                                <span
                                  key={filter}
                                  className="inline-flex items-center px-2 py-1 bg-secondary text-secondary-foreground rounded text-xs"
                                >
                                  {filter}
                                </span>
                              ),
                            )
                          ) : (
                            <p className="text-sm text-muted-foreground">
                              None
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Filters determine which transaction descriptions will
                    trigger notifications. Add terms to exclude transactions
                    containing those words.
                  </p>
                </div>
              ) : (
                <div className="text-center py-8">
                  <Filter className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-foreground mb-2">
                    No notification filters configured
                  </h3>
                  <p className="text-muted-foreground mb-4">
                    Set up filters to control which transactions trigger
                    notifications.
                  </p>
                  <NotificationFiltersDrawer settings={notificationSettings} />
                </div>
              )}
            </CardContent>
          </Card>
          {/* S3 Backup Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Cloud className="h-5 w-5 text-primary" />
                <span>S3 Backup Configuration</span>
              </CardTitle>
              <CardDescription>
                Configure automatic database backups to Amazon S3 or
                S3-compatible storage
              </CardDescription>
            </CardHeader>

            <CardContent>
              {!backupSettings?.s3 ? (
                <div className="text-center py-8">
                  <Cloud className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-foreground mb-2">
                    No S3 backup configured
                  </h3>
                  <p className="text-muted-foreground mb-4">
                    Set up S3 backup to automatically backup your database to
                    the cloud.
                  </p>
                  <S3BackupConfigDrawer settings={backupSettings} />
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="p-6 hover:bg-accent transition-colors">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                      <div className="flex items-center space-x-4 min-w-0">
                        <div className="p-3 bg-muted rounded-full flex-shrink-0">
                          <Cloud className="h-6 w-6 text-muted-foreground" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-3">
                            <h4 className="text-lg font-medium text-foreground">
                              S3 Backup
                            </h4>
                            <div className="flex items-center space-x-2">
                              <div
                                className={`w-2 h-2 rounded-full ${
                                  backupSettings.s3.enabled
                                    ? "bg-green-500"
                                    : "bg-muted-foreground"
                                }`}
                              />
                              <span className="text-sm text-muted-foreground">
                                {backupSettings.s3.enabled
                                  ? "Enabled"
                                  : "Disabled"}
                              </span>
                            </div>
                          </div>
                          <p className="text-sm text-muted-foreground mt-1 truncate">
                            {backupSettings.s3.bucket_name} ({backupSettings.s3.region})
                            {backupSettings.s3.endpoint_url && ` • ${backupSettings.s3.endpoint_url}`}
                          </p>
                        </div>
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={handleCreateBackup}
                          disabled={createBackupMutation.isPending}
                        >
                          {createBackupMutation.isPending ? (
                            <>
                              <Archive className="h-4 w-4 mr-2 animate-spin" />
                              Creating...
                            </>
                          ) : (
                            <>
                              <Archive className="h-4 w-4 mr-2" />
                              Backup Now
                            </>
                          )}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={handleViewBackups}
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View Backups
                        </Button>
                        <S3BackupConfigDrawer settings={backupSettings} />
                      </div>
                    </div>
                  </div>

                  {/* Backup List Modal/View */}
                  {showBackups && (
                    <div className="mt-6 p-4 border rounded-lg bg-background">
                      <div className="flex items-center justify-between mb-4">
                        <h5 className="font-medium">Available Backups</h5>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setShowBackups(false)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>

                      {backupsLoading ? (
                        <p className="text-sm text-muted-foreground">Loading backups...</p>
                      ) : backupsError ? (
                        <div className="space-y-2">
                          <p className="text-sm text-destructive">Failed to load backups</p>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => refetchBackups()}
                          >
                            <RefreshCw className="h-4 w-4 mr-2" />
                            Retry
                          </Button>
                        </div>
                      ) : !backups || backups.length === 0 ? (
                        <p className="text-sm text-muted-foreground">No backups found</p>
                      ) : (
                        <div className="space-y-2">
                          {backups.map((backup, index) => (
                            <div
                              key={backup.key || index}
                              className="flex items-center justify-between p-3 border rounded bg-muted/50"
                            >
                              <div>
                                <p className="text-sm font-medium">{backup.key}</p>
                                <div className="flex items-center space-x-4 text-xs text-muted-foreground mt-1">
                                  <span>Modified: {formatDate(backup.last_modified)}</span>
                                  <span>Size: {(backup.size / 1024 / 1024).toFixed(2)} MB</span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
    </div>
  );
}
