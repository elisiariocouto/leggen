import { useQuery } from "@tanstack/react-query";
import {
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Activity,
  Clock,
  TrendingUp,
  User,
} from "lucide-react";
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
import type { SyncOperationsResponse } from "../types/api";

export default function System() {
  const {
    data: syncOperations,
    isLoading: syncOperationsLoading,
    error: syncOperationsError,
    refetch: refetchSyncOperations,
  } = useQuery<SyncOperationsResponse>({
    queryKey: ["syncOperations"],
    queryFn: () => apiClient.getSyncOperations(10, 0), // Get latest 10 operations
  });

  if (syncOperationsLoading) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-center">
              <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
              <span className="ml-2 text-muted-foreground">Loading system status...</span>
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
              Unable to connect to the Leggen API. Please check your configuration
              and ensure the API server is running.
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
          <CardTitle className="flex items-center space-x-2">
            <Activity className="h-5 w-5 text-primary" />
            <span>Recent Sync Operations</span>
          </CardTitle>
          <CardDescription>Latest synchronization activities and their status</CardDescription>
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
              {syncOperations.operations.slice(0, 10).map((operation) => {
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

      {/* System Health Summary Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <span>System Health</span>
          </CardTitle>
          <CardDescription>Overall system status and performance</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="text-2xl font-bold text-green-700">
                {syncOperations?.operations.filter(op => op.success).length || 0}
              </div>
              <div className="text-sm text-green-600">Successful Syncs</div>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg border border-red-200">
              <div className="text-2xl font-bold text-red-700">
                {syncOperations?.operations.filter(op => !op.success && op.completed_at).length || 0}
              </div>
              <div className="text-sm text-red-600">Failed Syncs</div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="text-2xl font-bold text-blue-700">
                {syncOperations?.operations.filter(op => !op.completed_at).length || 0}
              </div>
              <div className="text-sm text-blue-600">Running Operations</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
