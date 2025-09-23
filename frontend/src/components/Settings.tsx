import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  CreditCard,
  TrendingUp,
  TrendingDown,
  Building2,
  RefreshCw,
  AlertCircle,
  Edit2,
  Check,
  X,
  Bell,
  MessageSquare,
  Send,
  Trash2,
  User,
  Filter,
  Cloud,
} from "lucide-react";
import { apiClient } from "../lib/api";
import { formatCurrency, formatDate } from "../lib/utils";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import AccountsSkeleton from "./AccountsSkeleton";
import NotificationFiltersDrawer from "./NotificationFiltersDrawer";
import DiscordConfigDrawer from "./DiscordConfigDrawer";
import TelegramConfigDrawer from "./TelegramConfigDrawer";
import AddBankAccountDrawer from "./AddBankAccountDrawer";
import S3BackupConfigDrawer from "./S3BackupConfigDrawer";
import type {
  Account,
  Balance,
  NotificationSettings,
  NotificationService,
  BackupSettings,
} from "../types/api";

// Helper function to get status indicator color and styles
const getStatusIndicator = (status: string) => {
  const statusLower = status.toLowerCase();

  switch (statusLower) {
    case "ready":
      return {
        color: "bg-green-500",
        tooltip: "Ready",
      };
    case "pending":
      return {
        color: "bg-amber-500",
        tooltip: "Pending",
      };
    case "error":
    case "failed":
      return {
        color: "bg-destructive",
        tooltip: "Error",
      };
    case "inactive":
      return {
        color: "bg-muted-foreground",
        tooltip: "Inactive",
      };
    default:
      return {
        color: "bg-primary",
        tooltip: status,
      };
  }
};

export default function Settings() {
  const [editingAccountId, setEditingAccountId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState("");
  const [failedImages, setFailedImages] = useState<Set<string>>(new Set());

  const queryClient = useQueryClient();

  // Account queries
  const {
    data: accounts,
    isLoading: accountsLoading,
    error: accountsError,
    refetch: refetchAccounts,
  } = useQuery<Account[]>({
    queryKey: ["accounts"],
    queryFn: apiClient.getAccounts,
  });

  const { data: balances } = useQuery<Balance[]>({
    queryKey: ["balances"],
    queryFn: () => apiClient.getBalances(),
  });

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

  const { data: bankConnections } = useQuery({
    queryKey: ["bankConnections"],
    queryFn: apiClient.getBankConnectionsStatus,
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

  // Account mutations
  const updateAccountMutation = useMutation({
    mutationFn: ({ id, display_name }: { id: string; display_name: string }) =>
      apiClient.updateAccount(id, { display_name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      setEditingAccountId(null);
      setEditingName("");
    },
    onError: (error) => {
      console.error("Failed to update account:", error);
    },
  });

  // Notification mutations
  const deleteServiceMutation = useMutation({
    mutationFn: apiClient.deleteNotificationService,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notificationSettings"] });
      queryClient.invalidateQueries({ queryKey: ["notificationServices"] });
    },
  });

  // Bank connection mutations
  const deleteBankConnectionMutation = useMutation({
    mutationFn: apiClient.deleteBankConnection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      queryClient.invalidateQueries({ queryKey: ["bankConnections"] });
      queryClient.invalidateQueries({ queryKey: ["balances"] });
    },
  });

  // Account handlers
  const handleEditStart = (account: Account) => {
    setEditingAccountId(account.id);
    setEditingName(account.display_name || account.name || "");
  };

  const handleEditSave = () => {
    if (editingAccountId && editingName.trim()) {
      updateAccountMutation.mutate({
        id: editingAccountId,
        display_name: editingName.trim(),
      });
    }
  };

  const handleEditCancel = () => {
    setEditingAccountId(null);
    setEditingName("");
  };

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

  const isLoading = accountsLoading || settingsLoading || servicesLoading || backupLoading;
  const hasError = accountsError || settingsError || servicesError || backupError;

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
              refetchAccounts();
              refetchSettings();
              refetchServices();
              refetchBackup();
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
      <Tabs defaultValue="accounts" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="accounts" className="flex items-center space-x-2">
            <User className="h-4 w-4" />
            <span>Accounts</span>
          </TabsTrigger>
          <TabsTrigger
            value="notifications"
            className="flex items-center space-x-2"
          >
            <Bell className="h-4 w-4" />
            <span>Notifications</span>
          </TabsTrigger>
          <TabsTrigger value="backup" className="flex items-center space-x-2">
            <Cloud className="h-4 w-4" />
            <span>Backup</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="accounts" className="space-y-6">
          {/* Account Management Section */}
          <Card>
            <CardHeader>
              <CardTitle>Account Management</CardTitle>
              <CardDescription>
                Manage your connected bank accounts and customize their display
                names
              </CardDescription>
            </CardHeader>

            {!accounts || accounts.length === 0 ? (
              <CardContent className="p-6 text-center">
                <CreditCard className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">
                  No accounts found
                </h3>
                <p className="text-muted-foreground mb-4">
                  Connect your first bank account to get started with Leggen.
                </p>
              </CardContent>
            ) : (
              <CardContent className="p-0">
                <div className="divide-y divide-border">
                  {accounts.map((account) => {
                    // Get balance from account's balances array or fallback to balances query
                    const accountBalance = account.balances?.[0];
                    const fallbackBalance = balances?.find(
                      (b) => b.account_id === account.id,
                    );
                    const balance =
                      accountBalance?.amount ||
                      fallbackBalance?.balance_amount ||
                      0;
                    const currency =
                      accountBalance?.currency ||
                      fallbackBalance?.currency ||
                      account.currency ||
                      "EUR";
                    const isPositive = balance >= 0;

                    return (
                      <div
                        key={account.id}
                        className="p-4 sm:p-6 hover:bg-accent transition-colors"
                      >
                        {/* Mobile layout - stack vertically */}
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
                          <div className="flex items-start sm:items-center space-x-3 sm:space-x-4 min-w-0 flex-1">
                            <div className="flex-shrink-0 w-10 h-10 sm:w-12 sm:h-12 rounded-full overflow-hidden bg-muted flex items-center justify-center">
                              {account.logo && !failedImages.has(account.id) ? (
                                <img
                                  src={account.logo}
                                  alt={`${account.institution_id} logo`}
                                  className="w-6 h-6 sm:w-8 sm:h-8 object-contain"
                                  onError={() => {
                                    console.warn(
                                      `Failed to load bank logo for ${account.institution_id}: ${account.logo}`,
                                    );
                                    setFailedImages(
                                      (prev) => new Set([...prev, account.id]),
                                    );
                                  }}
                                />
                              ) : (
                                <Building2 className="h-5 w-5 sm:h-6 sm:w-6 text-muted-foreground" />
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              {editingAccountId === account.id ? (
                                <div className="space-y-2">
                                  <div className="flex items-center space-x-2">
                                    <input
                                      type="text"
                                      value={editingName}
                                      onChange={(e) =>
                                        setEditingName(e.target.value)
                                      }
                                      className="flex-1 px-3 py-1 text-base sm:text-lg font-medium border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring"
                                      placeholder="Custom account name"
                                      name="search"
                                      autoComplete="off"
                                      onKeyDown={(e) => {
                                        if (e.key === "Enter") handleEditSave();
                                        if (e.key === "Escape")
                                          handleEditCancel();
                                      }}
                                      autoFocus
                                    />
                                    <button
                                      onClick={handleEditSave}
                                      disabled={
                                        !editingName.trim() ||
                                        updateAccountMutation.isPending
                                      }
                                      className="p-1 text-green-600 hover:text-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                      title="Save changes"
                                    >
                                      <Check className="h-4 w-4" />
                                    </button>
                                    <button
                                      onClick={handleEditCancel}
                                      className="p-1 text-gray-600 hover:text-gray-700"
                                      title="Cancel editing"
                                    >
                                      <X className="h-4 w-4" />
                                    </button>
                                  </div>
                                  <p className="text-sm text-muted-foreground truncate">
                                    {account.institution_id}
                                  </p>
                                </div>
                              ) : (
                                <div>
                                  <div className="flex items-center space-x-2 min-w-0">
                                    <h4 className="text-base sm:text-lg font-medium text-foreground truncate">
                                      {account.display_name ||
                                        account.name ||
                                        "Unnamed Account"}
                                    </h4>
                                    <button
                                      onClick={() => handleEditStart(account)}
                                      className="flex-shrink-0 p-1 text-muted-foreground hover:text-foreground transition-colors"
                                      title="Edit account name"
                                    >
                                      <Edit2 className="h-4 w-4" />
                                    </button>
                                  </div>
                                  <p className="text-sm text-muted-foreground truncate">
                                    {account.institution_id}
                                  </p>
                                  {account.iban && (
                                    <p className="text-xs text-muted-foreground mt-1 font-mono break-all sm:break-normal">
                                      IBAN: {account.iban}
                                    </p>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Balance and date section */}
                          <div className="flex items-center justify-between sm:flex-col sm:items-end sm:text-right flex-shrink-0">
                            {/* Date and status indicator - left on mobile, bottom on desktop */}
                            <div className="flex items-center space-x-2 order-1 sm:order-2">
                              <div
                                className={`w-3 h-3 rounded-full ${getStatusIndicator(account.status).color} relative group cursor-help`}
                                role="img"
                                aria-label={`Account status: ${getStatusIndicator(account.status).tooltip}`}
                              >
                                {/* Tooltip */}
                                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block bg-gray-900 text-white text-xs rounded py-1 px-2 whitespace-nowrap z-10">
                                  {getStatusIndicator(account.status).tooltip}
                                  <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-2 border-transparent border-t-gray-900"></div>
                                </div>
                              </div>
                              <p className="text-xs sm:text-sm text-muted-foreground whitespace-nowrap">
                                Updated{" "}
                                {formatDate(
                                  account.last_accessed || account.created,
                                )}
                              </p>
                            </div>

                            {/* Balance - right on mobile, top on desktop */}
                            <div className="flex items-center space-x-2 order-2 sm:order-1">
                              {isPositive ? (
                                <TrendingUp className="h-4 w-4 text-green-500" />
                              ) : (
                                <TrendingDown className="h-4 w-4 text-red-500" />
                              )}
                              <p
                                className={`text-base sm:text-lg font-semibold ${
                                  isPositive ? "text-green-600" : "text-red-600"
                                }`}
                              >
                                {formatCurrency(balance, currency)}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            )}
          </Card>

          {/* Bank Connections Status */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Bank Connections</CardTitle>
                  <CardDescription>
                    Status of all bank connection requests and their
                    authorization state
                  </CardDescription>
                </div>
                <AddBankAccountDrawer />
              </div>
            </CardHeader>

            {!bankConnections || bankConnections.length === 0 ? (
              <CardContent className="p-6 text-center">
                <Building2 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">
                  No bank connections found
                </h3>
                <p className="text-muted-foreground">
                  Bank connection requests will appear here after you connect
                  accounts.
                </p>
              </CardContent>
            ) : (
              <CardContent className="p-0">
                <div className="divide-y divide-border">
                  {bankConnections.map((connection) => {
                    const statusColor =
                      connection.status.toLowerCase() === "ln"
                        ? "bg-green-500"
                        : connection.status.toLowerCase() === "cr"
                          ? "bg-amber-500"
                          : connection.status.toLowerCase() === "ex"
                            ? "bg-red-500"
                            : "bg-muted-foreground";

                    return (
                      <div
                        key={connection.requisition_id}
                        className="p-4 sm:p-6 hover:bg-accent transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4 min-w-0 flex-1">
                            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-muted flex items-center justify-center">
                              <Building2 className="h-5 w-5 text-muted-foreground" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center space-x-2">
                                <h4 className="text-base font-medium text-foreground truncate">
                                  {connection.bank_name}
                                </h4>
                                <div
                                  className={`w-3 h-3 rounded-full ${statusColor}`}
                                  title={connection.status_display}
                                />
                              </div>
                              <p className="text-sm text-muted-foreground">
                                {connection.status_display} •{" "}
                                {connection.accounts_count} account
                                {connection.accounts_count !== 1 ? "s" : ""}
                              </p>
                              <p className="text-xs text-muted-foreground font-mono">
                                ID: {connection.requisition_id}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center space-x-2 flex-shrink-0">
                            <div className="text-right">
                              <p className="text-xs text-muted-foreground">
                                Created {formatDate(connection.created_at)}
                              </p>
                            </div>
                            <button
                              onClick={() => {
                                const isWorking =
                                  connection.status.toLowerCase() === "ln";
                                const message = isWorking
                                  ? `Are you sure you want to disconnect "${connection.bank_name}"? This will stop syncing new transactions but keep your existing transaction history.`
                                  : `Delete connection to ${connection.bank_name}?`;

                                if (confirm(message)) {
                                  deleteBankConnectionMutation.mutate(
                                    connection.requisition_id,
                                  );
                                }
                              }}
                              disabled={deleteBankConnectionMutation.isPending}
                              className="p-1 text-muted-foreground hover:text-destructive transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                              title="Delete connection"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-6">
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
                              (filter, index) => (
                                <span
                                  key={index}
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
                              (filter, index) => (
                                <span
                                  key={index}
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
        </TabsContent>

        <TabsContent value="backup" className="space-y-6">
          {/* S3 Backup Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Cloud className="h-5 w-5 text-primary" />
                <span>S3 Backup Configuration</span>
              </CardTitle>
              <CardDescription>
                Configure automatic database backups to Amazon S3 or S3-compatible storage
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
                    Set up S3 backup to automatically backup your database to the cloud.
                  </p>
                  <S3BackupConfigDrawer settings={backupSettings} />
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="p-3 bg-muted rounded-full">
                        <Cloud className="h-6 w-6 text-muted-foreground" />
                      </div>
                      <div>
                        <div className="flex items-center space-x-3">
                          <h4 className="text-lg font-medium text-foreground">
                            S3 Backup
                          </h4>
                          <div className="flex items-center space-x-2">
                            <div className={`w-2 h-2 rounded-full ${
                              backupSettings.s3.enabled
                                ? 'bg-green-500'
                                : 'bg-muted-foreground'
                            }`} />
                            <span className="text-sm text-muted-foreground">
                              {backupSettings.s3.enabled ? 'Enabled' : 'Disabled'}
                            </span>
                          </div>
                        </div>
                        <div className="mt-2 space-y-1">
                          <p className="text-sm text-muted-foreground">
                            <span className="font-medium">Bucket:</span> {backupSettings.s3.bucket_name}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            <span className="font-medium">Region:</span> {backupSettings.s3.region}
                          </p>
                          {backupSettings.s3.endpoint_url && (
                            <p className="text-sm text-muted-foreground">
                              <span className="font-medium">Endpoint:</span> {backupSettings.s3.endpoint_url}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                    <S3BackupConfigDrawer settings={backupSettings} />
                  </div>
                  
                  <div className="p-4 bg-muted rounded-lg">
                    <h5 className="font-medium mb-2">Backup Information</h5>
                    <p className="text-sm text-muted-foreground mb-3">
                      Database backups are stored in the "leggen_backups/" folder in your S3 bucket.
                      Backups include the complete SQLite database file.
                    </p>
                    <div className="flex space-x-2">
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => {
                          // TODO: Implement manual backup trigger
                          console.log("Manual backup triggered");
                        }}
                      >
                        Create Backup Now
                      </Button>
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => {
                          // TODO: Implement backup list view
                          console.log("View backups");
                        }}
                      >
                        View Backups
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
