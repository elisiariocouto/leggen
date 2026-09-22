import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Archive, Cloud, Eye, History, RefreshCw, X } from "lucide-react";
import { toast } from "sonner";
import { apiClient, getApiErrorMessage } from "../../lib/api";
import { invalidateSyncedData, queryKeys } from "../../lib/queryKeys";
import { formatDateTime } from "../../lib/utils";
import { Button } from "../ui/button";
import { CardContent } from "../ui/card";
import ConfirmDialog from "../ConfirmDialog";
import SettingsCard from "./SettingsCard";
import S3BackupConfigDrawer from "./S3BackupConfigDrawer";
import type { BackupInfo } from "../../types/api";

/** The backups in the bucket, each with a Restore button behind a confirmation. */
function BackupList({ onClose }: { onClose: () => void }) {
  const [restoreTarget, setRestoreTarget] = useState<BackupInfo | null>(null);
  const queryClient = useQueryClient();

  const {
    data: backups,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: queryKeys.backups,
    queryFn: apiClient.listBackups,
  });

  const restore = useMutation({
    mutationFn: (backupKey: string) =>
      apiClient.performBackupOperation({
        operation: "restore",
        backup_key: backupKey,
      }),
    onSuccess: (response) => {
      if (response.completed) {
        // The restore swapped the whole database, so everything derived from
        // it is stale — categories included, which a sync would not touch.
        invalidateSyncedData(queryClient);
        queryClient.invalidateQueries({ queryKey: queryKeys.categories });
        setRestoreTarget(null);
        toast.success("Database restored successfully!");
      } else {
        toast.error("Failed to restore backup.");
      }
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to restore backup."));
    },
  });

  return (
    <div className="mt-6 p-4 border rounded-lg bg-background">
      <div className="flex items-center justify-between mb-4">
        <h5 className="font-medium">Available Backups</h5>
        <Button
          size="sm"
          variant="ghost"
          aria-label="Close backup list"
          onClick={onClose}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading backups...</p>
      ) : error ? (
        <div className="space-y-2">
          <p className="text-sm text-destructive">Failed to load backups</p>
          <Button size="sm" variant="outline" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      ) : !backups || backups.length === 0 ? (
        <p className="text-sm text-muted-foreground">No backups found</p>
      ) : (
        <div className="space-y-2">
          {backups.map((backup) => (
            <div
              key={backup.key}
              className="flex items-center justify-between p-3 border rounded bg-muted/50"
            >
              <div className="min-w-0">
                <p className="text-sm font-medium truncate">{backup.key}</p>
                <div className="flex items-center space-x-4 text-xs text-muted-foreground mt-1">
                  <span>Modified: {formatDateTime(backup.last_modified)}</span>
                  <span>Size: {(backup.size / 1024 / 1024).toFixed(2)} MB</span>
                </div>
              </div>
              <Button
                size="sm"
                variant="outline"
                className="shrink-0 ml-4"
                onClick={() => setRestoreTarget(backup)}
                disabled={restore.isPending}
              >
                <History className="h-4 w-4 mr-2" />
                Restore
              </Button>
            </div>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={!!restoreTarget}
        onClose={() => setRestoreTarget(null)}
        onConfirm={() => {
          if (restoreTarget?.key) {
            restore.mutate(restoreTarget.key);
          }
        }}
        isPending={restore.isPending}
        title="Restore Database"
        description={
          <span className="block space-y-2">
            <span className="block">
              This replaces the current database with the backup taken on{" "}
              <span className="font-medium text-foreground">
                {restoreTarget ? formatDateTime(restoreTarget.last_modified) : ""}
              </span>
              . Accounts, transactions and categories recorded since then will
              be lost.
            </span>
            <span className="block break-all text-xs">{restoreTarget?.key}</span>
            <span className="block font-medium text-foreground">
              This cannot be undone. Consider running a backup first.
            </span>
          </span>
        }
        confirmLabel="Restore"
        pendingLabel="Restoring..."
      />
    </div>
  );
}

export default function BackupCard() {
  const [showBackups, setShowBackups] = useState(false);
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: queryKeys.backupSettings,
    queryFn: apiClient.getBackupSettings,
  });

  const createBackup = useMutation({
    mutationFn: () => apiClient.performBackupOperation({ operation: "backup" }),
    onSuccess: (response) => {
      if (response.completed) {
        toast.success("Backup created successfully!");
        queryClient.invalidateQueries({ queryKey: queryKeys.backups });
      } else {
        toast.error("Failed to create backup.");
      }
    },
    onError: (error) => {
      toast.error(
        getApiErrorMessage(
          error,
          "Failed to create backup. Please check your S3 configuration.",
        ),
      );
    },
  });

  // Both actions need a bucket to talk to.
  const requireEnabled = (action: () => void) => () => {
    if (!query.data?.s3?.enabled) {
      toast.error(
        "S3 backup is not enabled. Please configure and enable S3 backup first.",
      );
      return;
    }
    action();
  };

  return (
    <SettingsCard
      icon={Cloud}
      title="S3 Backup Configuration"
      description="Configure automatic database backups to Amazon S3 or S3-compatible storage"
      query={query}
    >
      {(backupSettings) => (
        <CardContent>
          {!backupSettings.s3 ? (
            <div className="text-center py-8">
              <Cloud className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">
                No S3 backup configured
              </h3>
              <p className="text-muted-foreground mb-4">
                Set up S3 backup to automatically backup your database to the
                cloud.
              </p>
              <S3BackupConfigDrawer settings={backupSettings} />
            </div>
          ) : (
            <div className="space-y-4">
              <div className="p-6 hover:bg-accent transition-colors">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div className="flex items-center space-x-4 min-w-0">
                    <div className="p-3 bg-muted rounded-full shrink-0">
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
                            aria-hidden="true"
                          />
                          <span className="text-sm text-muted-foreground">
                            {backupSettings.s3.enabled ? "Enabled" : "Disabled"}
                          </span>
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1 truncate">
                        {backupSettings.s3.bucket_name} ({backupSettings.s3.region})
                        {backupSettings.s3.endpoint_url &&
                          ` • ${backupSettings.s3.endpoint_url}`}
                      </p>
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={requireEnabled(() => createBackup.mutate())}
                      disabled={createBackup.isPending}
                    >
                      <Archive
                        className={`h-4 w-4 mr-2 ${createBackup.isPending ? "animate-spin" : ""}`}
                      />
                      {createBackup.isPending ? "Creating..." : "Backup Now"}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={requireEnabled(() => setShowBackups(true))}
                    >
                      <Eye className="h-4 w-4 mr-2" />
                      View Backups
                    </Button>
                    <S3BackupConfigDrawer settings={backupSettings} />
                  </div>
                </div>
              </div>

              {showBackups && <BackupList onClose={() => setShowBackups(false)} />}
            </div>
          )}
        </CardContent>
      )}
    </SettingsCard>
  );
}
