import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Cloud, TestTube, Trash2 } from "lucide-react";
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
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "./ui/alert-dialog";
import type { BackupSettings, S3Config } from "../types/api";

interface S3BackupConfigDrawerProps {
  settings?: BackupSettings;
  trigger?: React.ReactNode;
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
  trigger,
}: S3BackupConfigDrawerProps) {
  const [open, setOpen] = useState(false);
  const [confirmRemove, setConfirmRemove] = useState(false);
  const [config, setConfig] = useState<S3Config>(EMPTY_S3_CONFIG);

  const queryClient = useQueryClient();

  useEffect(() => {
    if (settings?.s3) {
      setConfig({ ...settings.s3 });
    } else {
      // Removing the configuration must not leave the old values in the form
      setConfig(EMPTY_S3_CONFIG);
    }
  }, [settings]);

  const updateMutation = useMutation({
    mutationFn: (s3Config: S3Config) =>
      apiClient.updateBackupSettings({
        s3: s3Config,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["backupSettings"] });
      setOpen(false);
      toast.success("S3 backup configuration saved successfully");
    },
    onError: (error) => {
      toast.error(
        getApiErrorMessage(
          error,
          "Failed to save S3 configuration. Please check your settings and try again.",
        ),
      );
    },
  });

  const deleteMutation = useMutation({
    mutationFn: apiClient.deleteBackupSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["backupSettings"] });
      queryClient.invalidateQueries({ queryKey: ["backups"] });
      setConfirmRemove(false);
      setOpen(false);
      toast.success("S3 backup configuration removed.");
    },
    onError: (error) => {
      toast.error(
        getApiErrorMessage(error, "Failed to remove S3 configuration."),
      );
    },
  });

  const testMutation = useMutation({
    mutationFn: () =>
      apiClient.testBackupConnection({
        service: "s3",
        config: config,
      }),
    onSuccess: (response) => {
      if (response.connected) {
        toast.success(
          "S3 connection test successful! Your configuration is working correctly.",
        );
      } else {
        toast.error(
          "S3 connection test failed. Please verify your credentials and settings.",
        );
      }
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate(config);
  };

  const handleTest = () => {
    testMutation.mutate();
  };

  const isConfigValid =
    config.access_key_id.trim().length > 0 &&
    config.secret_access_key.trim().length > 0 &&
    config.bucket_name.trim().length > 0;

  return (
    <Drawer open={open} onOpenChange={setOpen}>
      <DrawerTrigger asChild>{trigger || <EditButton />}</DrawerTrigger>
      <DrawerContent>
        <div className="mx-auto w-full max-w-sm">
          <DrawerHeader>
            <DrawerTitle className="flex items-center space-x-2">
              <Cloud className="h-5 w-5 text-primary" />
              <span>S3 Backup Configuration</span>
            </DrawerTitle>
            <DrawerDescription>
              Configure S3 settings for automatic database backups
            </DrawerDescription>
          </DrawerHeader>

          <form onSubmit={handleSubmit} className="px-4 space-y-4">
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
              {settings?.s3 && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setConfirmRemove(true)}
                  disabled={deleteMutation.isPending}
                  className="text-destructive hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Remove configuration
                </Button>
              )}
              <DrawerClose asChild>
                <Button variant="ghost">Cancel</Button>
              </DrawerClose>
            </DrawerFooter>
          </form>
        </div>
      </DrawerContent>

      <AlertDialog
        open={confirmRemove}
        onOpenChange={(next) => {
          if (!next) {
            setConfirmRemove(false);
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove S3 Configuration</AlertDialogTitle>
            <AlertDialogDescription>
              This deletes the bucket settings and the stored credentials.
              Scheduled backups will stop until S3 is configured again. Existing
              backups in the bucket are not touched.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteMutation.mutate()}
              disabled={deleteMutation.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Remove
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Drawer>
  );
}
