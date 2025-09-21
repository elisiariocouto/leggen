import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Bell,
  MessageSquare,
  Send,
  Trash2,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Settings,
  TestTube,
  Activity,
  Clock,
  TrendingUp,
  User,
} from "lucide-react";
import { apiClient } from "../lib/api";
import NotificationsSkeleton from "./NotificationsSkeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Badge } from "./ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import type { NotificationSettings, NotificationService, SyncOperationsResponse } from "../types/api";

export default function Notifications() {
  const [testService, setTestService] = useState("");
  const [testMessage, setTestMessage] = useState(
    "Test notification from Leggen",
  );
  const queryClient = useQueryClient();

  const {
    data: settings,
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

  const {
    data: syncOperations,
    isLoading: syncOperationsLoading,
    error: syncOperationsError,
    refetch: refetchSyncOperations,
  } = useQuery<SyncOperationsResponse>({
    queryKey: ["syncOperations"],
    queryFn: () => apiClient.getSyncOperations(10, 0), // Get latest 10 operations
  });

  const testMutation = useMutation({
    mutationFn: apiClient.testNotification,
    onSuccess: () => {
      // Could show a success toast here
      console.log("Test notification sent successfully");
    },
    onError: (error) => {
      console.error("Failed to send test notification:", error);
    },
  });

  const deleteServiceMutation = useMutation({
    mutationFn: apiClient.deleteNotificationService,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notificationSettings"] });
      queryClient.invalidateQueries({ queryKey: ["notificationServices"] });
    },
  });

  if (settingsLoading || servicesLoading || syncOperationsLoading) {
    return <NotificationsSkeleton />;
  }

  if (settingsError || servicesError || syncOperationsError) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Failed to load system data</AlertTitle>
        <AlertDescription className="space-y-3">
          <p>
            Unable to connect to the Leggen API. Please check your configuration
            and ensure the API server is running.
          </p>
          <Button
            onClick={() => {
              refetchSettings();
              refetchServices();
              refetchSyncOperations();
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

  const handleTestNotification = () => {
    if (!testService) return;

    testMutation.mutate({
      service: testService.toLowerCase(),
      message: testMessage,
    });
  };

  const handleDeleteService = (serviceName: string) => {
    if (
      confirm(
        `Are you sure you want to delete the ${serviceName} notification service?`,
      )
    ) {
      deleteServiceMutation.mutate(serviceName.toLowerCase());
    }
  };

  return (
    <div className="space-y-6">
      {/* Sync Operations Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="h-5 w-5 text-primary" />
            <span>Sync Operations</span>
          </CardTitle>
          <CardDescription>Recent synchronization activities</CardDescription>
        </CardHeader>
        <CardContent>
          {!syncOperations || syncOperations.operations.length === 0 ? (
            <div className="text-center py-6">
              <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">
                No sync operations yet
              </h3>
              <p className="text-muted-foreground">
                Sync operations will appear here once you start syncing your accounts.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {syncOperations.operations.slice(0, 5).map((operation) => {
                const startedAt = new Date(operation.started_at);
                const isRunning = !operation.completed_at;
                const duration = operation.duration_seconds 
                  ? `${Math.round(operation.duration_seconds)}s`
                  : '';

                return (
                  <div
                    key={operation.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent transition-colors"
                  >
                    <div className="flex items-center space-x-4">
                      <div className={`p-2 rounded-full ${
                        isRunning 
                          ? 'bg-blue-100 text-blue-600' 
                          : operation.success 
                            ? 'bg-green-100 text-green-600' 
                            : 'bg-red-100 text-red-600'
                      }`}>
                        {isRunning ? (
                          <RefreshCw className="h-4 w-4 animate-spin" />
                        ) : operation.success ? (
                          <CheckCircle className="h-4 w-4" />
                        ) : (
                          <AlertCircle className="h-4 w-4" />
                        )}
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <h4 className="text-sm font-medium text-foreground">
                            {isRunning ? 'Sync Running' : operation.success ? 'Sync Completed' : 'Sync Failed'}
                          </h4>
                          <Badge variant="outline" className="text-xs">
                            {operation.trigger_type}
                          </Badge>
                        </div>
                        <div className="flex items-center space-x-4 mt-1 text-xs text-muted-foreground">
                          <span className="flex items-center space-x-1">
                            <Clock className="h-3 w-3" />
                            <span>{startedAt.toLocaleDateString()} {startedAt.toLocaleTimeString()}</span>
                          </span>
                          {duration && (
                            <span>Duration: {duration}</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="text-right text-sm text-muted-foreground">
                      <div className="flex items-center space-x-2">
                        <User className="h-3 w-3" />
                        <span>{operation.accounts_processed} accounts</span>
                      </div>
                      <div className="flex items-center space-x-2 mt-1">
                        <TrendingUp className="h-3 w-3" />
                        <span>{operation.transactions_added} new transactions</span>
                      </div>
                      {operation.errors.length > 0 && (
                        <div className="flex items-center space-x-2 mt-1 text-red-600">
                          <AlertCircle className="h-3 w-3" />
                          <span>{operation.errors.length} errors</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Test Notification Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <TestTube className="h-5 w-5 text-primary" />
            <span>Test Notifications</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="service" className="text-foreground">
                Service
              </Label>
              <Select value={testService} onValueChange={setTestService}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a service..." />
                </SelectTrigger>
                <SelectContent>
                  {services?.map((service) => (
                    <SelectItem key={service.name} value={service.name}>
                      {service.name}{" "}
                      {service.enabled ? "(Enabled)" : "(Disabled)"}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="message" className="text-foreground">
                Message
              </Label>
              <Input
                id="message"
                type="text"
                value={testMessage}
                onChange={(e) => setTestMessage(e.target.value)}
                placeholder="Test message..."
              />
            </div>
          </div>

          <div className="mt-4">
            <Button
              onClick={handleTestNotification}
              disabled={!testService || testMutation.isPending}
            >
              <Send className="h-4 w-4 mr-2" />
              {testMutation.isPending ? "Sending..." : "Send Test Notification"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Notification Services */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Bell className="h-5 w-5 text-primary" />
            <span>Notification Services</span>
          </CardTitle>
          <CardDescription>Manage your notification services</CardDescription>
        </CardHeader>

        {!services || services.length === 0 ? (
          <CardContent className="text-center">
            <Bell className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              No notification services configured
            </h3>
            <p className="text-muted-foreground">
              Configure notification services in your backend to receive alerts.
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
                        ) : service.name.toLowerCase().includes("telegram") ? (
                          <Send className="h-6 w-6 text-muted-foreground" />
                        ) : (
                          <Bell className="h-6 w-6 text-muted-foreground" />
                        )}
                      </div>
                      <div>
                        <h4 className="text-lg font-medium text-foreground capitalize">
                          {service.name}
                        </h4>
                        <div className="flex items-center space-x-2 mt-1">
                          <Badge
                            variant={
                              service.enabled ? "default" : "destructive"
                            }
                          >
                            {service.enabled ? (
                              <CheckCircle className="h-3 w-3 mr-1" />
                            ) : (
                              <AlertCircle className="h-3 w-3 mr-1" />
                            )}
                            {service.enabled ? "Enabled" : "Disabled"}
                          </Badge>
                          <Badge
                            variant={
                              service.configured ? "secondary" : "outline"
                            }
                          >
                            {service.configured
                              ? "Configured"
                              : "Not Configured"}
                          </Badge>
                        </div>
                      </div>
                    </div>

                    <Button
                      onClick={() => handleDeleteService(service.name)}
                      disabled={deleteServiceMutation.isPending}
                      variant="ghost"
                      size="sm"
                      className="text-destructive hover:text-destructive hover:bg-destructive/10"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        )}
      </Card>

      {/* Notification Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5 text-primary" />
            <span>Notification Settings</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {settings && (
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-foreground mb-2">
                  Filters
                </h4>
                <div className="bg-muted rounded-md p-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <Label className="text-xs font-medium text-muted-foreground mb-1 block">
                        Case Insensitive Filters
                      </Label>
                      <p className="text-sm text-foreground">
                        {settings.filters.case_insensitive.length > 0
                          ? settings.filters.case_insensitive.join(", ")
                          : "None"}
                      </p>
                    </div>
                    <div>
                      <Label className="text-xs font-medium text-muted-foreground mb-1 block">
                        Case Sensitive Filters
                      </Label>
                      <p className="text-sm text-foreground">
                        {settings.filters.case_sensitive &&
                        settings.filters.case_sensitive.length > 0
                          ? settings.filters.case_sensitive.join(", ")
                          : "None"}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="text-sm text-muted-foreground">
                <p>
                  Configure notification settings through your backend API to
                  customize filters and service configurations.
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
