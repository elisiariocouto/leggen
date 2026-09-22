import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Cloud, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { apiClient, getApiErrorMessage, MASKED_SECRET } from "../../lib/api";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Switch } from "../ui/switch";
import SettingsDrawer, {
  TestButton,
  useSettingsDrawer,
  useSettingsMutation,
} from "./SettingsDrawer";
import ConfirmDialog from "../ConfirmDialog";
import type { BackupSettings, S3Config } from "../../types/api";
import { queryKeys } from "../../lib/queryKeys";

interface S3BackupConfigDrawerProps {
  settings?: BackupSettings;
}

const EMPTY_S3_CONFIG: S3Config = {
  access_key_id: "",
  secret_access_key: "",
  bucket_name: "",
  region: "us-east-1",
  endpoint_url: "",
  path_style: false,
  enabled: true,
};

export default function S3BackupConfigDrawer({
  settings,
}: S3BackupConfigDrawerProps) {
  const [confirmRemove, setConfirmRemove] = useState(false);
  const [config, setConfig] = useState<S3Config>(EMPTY_S3_CONFIG);

  // Falling back to EMPTY_S3_CONFIG means removing the configuration does not
  // leave the old values sitting in the form.
  const drawer = useSettingsDrawer(() =>
    setConfig(settings?.s3 ? { ...settings.s3 } : EMPTY_S3_CONFIG),
  );

  const save = useSettingsMutation({
    mutationFn: (s3: S3Config) => apiClient.updateBackupSettings({ s3 }),
    invalidates: [queryKeys.backupSettings],
    successMessage: "S3 backup configuration saved successfully",
    errorMessage:
      "Failed to save S3 configuration. Please check your settings and try again.",
    onSuccess: drawer.close,
  });

  const remove = useSettingsMutation({
    mutationFn: apiClient.deleteBackupSettings,
    invalidates: [queryKeys.backupSettings, queryKeys.backups],
    successMessage: "S3 backup configuration removed.",
    errorMessage: "Failed to remove S3 configuration.",
    onSuccess: () => {
      setConfirmRemove(false);
      drawer.close();
    },
  });

  const test = useMutation({
    mutationFn: () => apiClient.testBackupConnection({ service: "s3", config }),
    onSuccess: () => {
      toast.success(
        "S3 connection test successful! Your configuration is working correctly.",
      );
    },
    onError: (error) => {
      toast.error(
        getApiErrorMessage(
          error,
          "S3 connection test failed. Please verify your credentials and settings.",
        ),
      );
    },
  });

  const isConfigValid =
    config.access_key_id.trim().length > 0 &&
    config.secret_access_key.trim().length > 0 &&
    config.bucket_name.trim().length > 0;

  return (
    <>
      <SettingsDrawer
        drawer={drawer}
        icon={Cloud}
        title="S3 Backup Configuration"
        description="Configure S3 settings for automatic database backups"
        width="sm"
        onSubmit={() => save.mutate(config)}
        isSaving={save.isPending}
        saveLabel="Save Configuration"
        actions={
          config.enabled &&
          isConfigValid && (
            <TestButton
              onClick={() => test.mutate()}
              isPending={test.isPending}
            />
          )
        }
        footer={
          settings?.s3 && (
            <Button
              type="button"
              variant="outline"
              onClick={() => setConfirmRemove(true)}
              disabled={remove.isPending}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Remove configuration
            </Button>
          )
        }
      >
        <div className="flex items-center space-x-2">
          <Switch
            id="enabled"
            checked={config.enabled}
            onCheckedChange={(checked) =>
              setConfig({ ...config, enabled: checked })
            }
          />
          <Label htmlFor="enabled">Enable S3 backups</Label>
        </div>

        {config.enabled && (
          <>
            <div className="space-y-2">
              <Label htmlFor="access_key_id">Access Key ID</Label>
              <Input
                id="access_key_id"
                type="text"
                value={config.access_key_id}
                onChange={(e) =>
                  setConfig({ ...config, access_key_id: e.target.value })
                }
                placeholder="Your AWS Access Key ID"
                required
              />
              {config.access_key_id === MASKED_SECRET && (
                <p className="text-xs text-muted-foreground">
                  A key is saved. Leave it unchanged to keep it.
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="secret_access_key">Secret Access Key</Label>
              <Input
                id="secret_access_key"
                type="password"
                value={config.secret_access_key}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    secret_access_key: e.target.value,
                  })
                }
                placeholder="Your AWS Secret Access Key"
                required
              />
              {config.secret_access_key === MASKED_SECRET && (
                <p className="text-xs text-muted-foreground">
                  A key is saved. Leave it unchanged to keep it.
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="bucket_name">Bucket Name</Label>
              <Input
                id="bucket_name"
                type="text"
                value={config.bucket_name}
                onChange={(e) =>
                  setConfig({ ...config, bucket_name: e.target.value })
                }
                placeholder="my-backup-bucket"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="region">Region</Label>
              <Input
                id="region"
                type="text"
                value={config.region}
                onChange={(e) =>
                  setConfig({ ...config, region: e.target.value })
                }
                placeholder="us-east-1"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="endpoint_url">
                Custom Endpoint URL (Optional)
              </Label>
              <Input
                id="endpoint_url"
                type="url"
                value={config.endpoint_url || ""}
                onChange={(e) =>
                  setConfig({ ...config, endpoint_url: e.target.value })
                }
                placeholder="https://custom-s3-endpoint.com"
              />
              <p className="text-xs text-muted-foreground">
                For S3-compatible services like MinIO or DigitalOcean Spaces
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="path_style"
                checked={config.path_style}
                onCheckedChange={(checked) =>
                  setConfig({ ...config, path_style: checked })
                }
              />
              <Label htmlFor="path_style">Use path-style addressing</Label>
            </div>
            <p className="text-xs text-muted-foreground">
              Enable for older S3 implementations or certain S3-compatible
              services
            </p>
          </>
        )}
      </SettingsDrawer>

      <ConfirmDialog
        open={confirmRemove}
        onClose={() => setConfirmRemove(false)}
        onConfirm={() => remove.mutate()}
        isPending={remove.isPending}
        title="Remove S3 Configuration"
        description="This deletes the bucket settings and the stored credentials. Scheduled backups will stop until S3 is configured again. Existing backups in the bucket are not touched."
        confirmLabel="Remove"
      />
    </>
  );
}
