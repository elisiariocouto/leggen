import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Activity,
  Clock,
  TrendingUp,
  User,
  FileText,
  ChevronDown,
} from "lucide-react";
import { toast } from "sonner";
import { apiClient } from "../lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./ui/dialog";
import { ScrollArea } from "./ui/scroll-area";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import type { SyncOperationsResponse, SyncOperation } from "../types/api";

// Component for viewing sync operation logs
function LogsDialog({ operation }: { operation: SyncOperation }) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="shrink-0">
          <FileText className="h-3 w-3 mr-1" />
          <span className="hidden sm:inline">View Logs</span>
          <span className="sm:hidden">Logs</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Sync Operation Logs</DialogTitle>
          <DialogDescription>
            Operation #{operation.id} - Started at{" "}
            {new Date(operation.started_at).toLocaleString()}
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="h-[60vh] w-full rounded border p-4">
          <div className="space-y-2">
            {operation.logs.length === 0 ? (
              <p className="text-muted-foreground text-sm">No logs available</p>
            ) : (
              operation.logs.map((log, index) => (
                <div
                  key={index}
                  className="text-sm font-mono bg-muted/50 p-2 rounded text-wrap break-all"
                >
                  {log}
                </div>
              ))
            )}
          </div>
          {operation.errors.length > 0 && (
            <>
              <div className="mt-4 mb-2 text-sm font-semibold text-destructive">
                Errors:
              </div>
              <div className="space-y-2">
                {operation.errors.map((error, index) => (
                  <div
                    key={index}
                    className="text-sm font-mono bg-destructive/10 border border-destructive/20 p-2 rounded text-wrap break-all text-destructive"
                  >
                    {error}
                  </div>
                ))}
              </div>
            </>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}

export default function Sync() {
  const queryClient = useQueryClient();

  const {
    data: syncOperations,
    isLoading: syncOperationsLoading,
    error: syncOperationsError,
    refetch: refetchSyncOperations,
  } = useQuery<SyncOperationsResponse>({
    queryKey: ["syncOperations"],
    queryFn: () => apiClient.getSyncOperations(10, 0), // Get latest 10 operations
  });

  const syncMutation = useMutation({
    mutationFn: (params?: { full_sync?: boolean }) =>
      apiClient.triggerSync(params),
    onSuccess: (result) => {
      if (result.success) {
        toast.success(
          `Sync completed: ${result.transactions_added} new transactions, ${result.accounts_processed} accounts processed.`,
        );
      } else {
        toast.error(
          `Sync finished with errors: ${result.errors.join(", ") || "Unknown error"}`,
        );
      }
      queryClient.invalidateQueries({ queryKey: ["syncOperations"] });
    },
    onError: () => {
      toast.error("Failed to trigger sync. Please try again.");
    },
  });

  // Compute summary counts
  const successCount =
    syncOperations?.operations.filter((op) => op.success).length || 0;
  const failedCount =
    syncOperations?.operations.filter((op) => !op.success && op.completed_at)
      .length || 0;
  const runningCount =
    syncOperations?.operations.filter((op) => !op.completed_at).length || 0;

  if (syncOperationsLoading) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-center">
              <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
              <span className="ml-2 text-muted-foreground">
                Loading system status...
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (syncOperationsError) {
    return (
      <div className="space-y-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Failed to load system data</AlertTitle>
          <AlertDescription className="space-y-3">
            <p>
              Unable to connect to the Leggen API. Please check your
              configuration and ensure the API server is running.
            </p>
            <Button
              onClick={() => refetchSyncOperations()}
              variant="outline"
              size="sm"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Sync Operations Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center space-x-2">
                <Activity className="h-5 w-5 text-primary" />
                <span>Recent Sync Operations</span>
              </CardTitle>
              <CardDescription className="mt-1.5">
                <span className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline" className="gap-1">
                    <CheckCircle className="h-3 w-3 text-green-600" />
                    {successCount} successful
                  </Badge>
                  <Badge variant="outline" className="gap-1">
                    <AlertCircle className="h-3 w-3 text-red-600" />
                    {failedCount} failed
                  </Badge>
                  {runningCount > 0 && (
                    <Badge variant="outline" className="gap-1">
                      <RefreshCw className="h-3 w-3 text-blue-600 animate-spin" />
                      {runningCount} running
                    </Badge>
                  )}
                </span>
              </CardDescription>
            </div>
            <div className="flex">
              <Button
                size="sm"
                onClick={() => syncMutation.mutate({})}
                disabled={syncMutation.isPending}
                className="rounded-r-none"
              >
                {syncMutation.isPending ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Syncing...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Sync Now
                  </>
                )}
              </Button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    size="sm"
                    disabled={syncMutation.isPending}
                    className="rounded-l-none border-l-0 px-2"
                  >
                    <ChevronDown className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem
                    onClick={() => syncMutation.mutate({})}
                  >
                    Last 30 days
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() =>
                      syncMutation.mutate({ full_sync: true })
                    }
                  >
                    Full history
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {!syncOperations || syncOperations.operations.length === 0 ? (
            <div className="text-center py-6">
              <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">
                No sync operations yet
              </h3>
              <p className="text-muted-foreground">
                Sync operations will appear here once you start syncing your
                accounts.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {syncOperations.operations.slice(0, 10).map((operation) => {
                const startedAt = new Date(operation.started_at);
                const isRunning = !operation.completed_at;
                const duration = operation.duration_seconds
                  ? `${Math.round(operation.duration_seconds)}s`
                  : "";

                return (
                  <div
                    key={operation.id}
                    className="border rounded-lg hover:bg-accent transition-colors"
                  >
                    {/* Desktop Layout */}
                    <div className="hidden md:flex items-center justify-between p-4">
                      <div className="flex items-center space-x-4">
                        <div
                          className={`p-2 rounded-full ${
                            isRunning
                              ? "bg-blue-100 dark:bg-blue-900/20 text-blue-600"
                              : operation.success
                                ? "bg-green-100 dark:bg-green-900/20 text-green-600"
                                : "bg-red-100 dark:bg-red-900/20 text-red-600"
                          }`}
                        >
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
                              {isRunning
                                ? "Sync Running"
                                : operation.success
                                  ? "Sync Completed"
                                  : "Sync Failed"}
                            </h4>
                            <Badge variant="outline" className="text-xs">
                              {operation.trigger_type.charAt(0).toUpperCase() +
                                operation.trigger_type.slice(1)}
                            </Badge>
                          </div>
                          <div className="flex items-center space-x-4 mt-1 text-xs text-muted-foreground">
                            <span className="flex items-center space-x-1">
                              <Clock className="h-3 w-3" />
                              <span>
                                {startedAt.toLocaleDateString()}{" "}
                                {startedAt.toLocaleTimeString()}
                              </span>
                            </span>
                            {duration && <span>Duration: {duration}</span>}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-right text-sm text-muted-foreground">
                          <div className="flex items-center space-x-2">
                            <User className="h-3 w-3" />
                            <span>{operation.accounts_processed} accounts</span>
                          </div>
                          <div className="flex items-center space-x-2 mt-1">
                            <TrendingUp className="h-3 w-3" />
                            <span>
                              {operation.transactions_added} new transactions
                            </span>
                          </div>
                        </div>
                        <LogsDialog operation={operation} />
                      </div>
                    </div>

                    {/* Mobile Layout */}
                    <div className="md:hidden p-4 space-y-3">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-3">
                          <div
                            className={`p-2 rounded-full ${
                              isRunning
                                ? "bg-blue-100 dark:bg-blue-900/20 text-blue-600"
                                : operation.success
                                  ? "bg-green-100 dark:bg-green-900/20 text-green-600"
                                  : "bg-red-100 dark:bg-red-900/20 text-red-600"
                            }`}
                          >
                            {isRunning ? (
                              <RefreshCw className="h-4 w-4 animate-spin" />
                            ) : operation.success ? (
                              <CheckCircle className="h-4 w-4" />
                            ) : (
                              <AlertCircle className="h-4 w-4" />
                            )}
                          </div>
                          <div>
                            <h4 className="text-sm font-medium text-foreground">
                              {isRunning
                                ? "Sync Running"
                                : operation.success
                                  ? "Sync Completed"
                                  : "Sync Failed"}
                            </h4>
                            <Badge variant="outline" className="text-xs mt-1">
                              {operation.trigger_type.charAt(0).toUpperCase() +
                                operation.trigger_type.slice(1)}
                            </Badge>
                          </div>
                        </div>
                        <LogsDialog operation={operation} />
                      </div>

                      <div className="text-xs text-muted-foreground space-y-2">
                        <div className="flex items-center space-x-1">
                          <Clock className="h-3 w-3" />
                          <span>
                            {startedAt.toLocaleDateString()}{" "}
                            {startedAt.toLocaleTimeString()}
                          </span>
                          {duration && (
                            <span className="ml-2">• {duration}</span>
                          )}
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="flex items-center space-x-1">
                            <User className="h-3 w-3" />
                            <span>{operation.accounts_processed} accounts</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <TrendingUp className="h-3 w-3" />
                            <span>
                              {operation.transactions_added} new transactions
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
