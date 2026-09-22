import { useState } from "react";
import { Plus, X } from "lucide-react";
import { apiClient } from "../../lib/api";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import SettingsDrawer, {
  useSettingsDrawer,
  useSettingsMutation,
} from "./SettingsDrawer";
import type { NotificationSettings, NotificationFilters } from "../../types/api";
import { queryKeys } from "../../lib/queryKeys";

interface NotificationFiltersDrawerProps {
  settings: NotificationSettings | undefined;
}

export default function NotificationFiltersDrawer({
  settings,
}: NotificationFiltersDrawerProps) {
  // Both lists are always present in local state; the API leaves them optional
  // so that an update can address one without clearing the other.
  const [filters, setFilters] = useState<{
    case_insensitive: string[];
    case_sensitive: string[];
  }>({
    case_insensitive: [],
    case_sensitive: [],
  });
  const [newCaseInsensitive, setNewCaseInsensitive] = useState("");
  const [newCaseSensitive, setNewCaseSensitive] = useState("");

  const drawer = useSettingsDrawer(() =>
    setFilters({
      case_insensitive: [...(settings?.filters?.case_insensitive || [])],
      case_sensitive: [...(settings?.filters?.case_sensitive || [])],
    }),
  );

  const save = useSettingsMutation({
    // The API merges a partial body, so only the filters are sent.
    mutationFn: (updated: NotificationFilters) =>
      apiClient.updateNotificationSettings({ filters: updated }),
    invalidates: [queryKeys.notificationSettings],
    successMessage: "Notification filters saved.",
    errorMessage: "Failed to update notification filters.",
    onSuccess: drawer.close,
  });

  const addCaseInsensitiveFilter = () => {
    if (
      newCaseInsensitive.trim() &&
      !filters.case_insensitive.includes(newCaseInsensitive.trim())
    ) {
      setFilters({
        ...filters,
        case_insensitive: [
          ...filters.case_insensitive,
          newCaseInsensitive.trim(),
        ],
      });
      setNewCaseInsensitive("");
    }
  };

  const addCaseSensitiveFilter = () => {
    if (
      newCaseSensitive.trim() &&
      !filters.case_sensitive?.includes(newCaseSensitive.trim())
    ) {
      setFilters({
        ...filters,
        case_sensitive: [
          ...(filters.case_sensitive || []),
          newCaseSensitive.trim(),
        ],
      });
      setNewCaseSensitive("");
    }
  };

  const removeCaseInsensitiveFilter = (index: number) => {
    setFilters({
      ...filters,
      case_insensitive: filters.case_insensitive.filter((_, i) => i !== index),
    });
  };

  const removeCaseSensitiveFilter = (index: number) => {
    setFilters({
      ...filters,
      case_sensitive:
        filters.case_sensitive?.filter((_, i) => i !== index) || [],
    });
  };

  return (
    <SettingsDrawer
      drawer={drawer}
      title="Notification Filters"
      description="Configure which transaction descriptions should trigger notifications"
      width="2xl"
      onSubmit={() => save.mutate(filters)}
      isSaving={save.isPending}
      saveLabel="Save Filters"
    >
      {/* Case Insensitive Filters */}
      <div className="space-y-3">
        <Label className="text-base font-medium">
          Case Insensitive Filters
        </Label>
        <p className="text-sm text-muted-foreground">
          Filters that match regardless of capitalization (e.g., "AMAZON"
          matches "amazon")
        </p>

        <div className="flex space-x-2">
          <Input
            placeholder="Add filter term..."
            value={newCaseInsensitive}
            onChange={(e) => setNewCaseInsensitive(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addCaseInsensitiveFilter();
              }
            }}
          />
          <Button
            type="button"
            onClick={addCaseInsensitiveFilter}
            size="sm"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex flex-wrap gap-2 min-h-8 p-3 bg-muted rounded-md">
          {filters.case_insensitive.length > 0 ? (
            filters.case_insensitive.map((filter, index) => (
              <div
                key={index}
                className="flex items-center space-x-1 bg-secondary text-secondary-foreground px-2 py-1 rounded-md text-sm"
              >
                <span>{filter}</span>
                <Button
                  type="button"
                  onClick={() => removeCaseInsensitiveFilter(index)}
                  variant="ghost"
                  size="icon"
                  className="h-5 w-5 hover:bg-secondary-foreground/10"
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            ))
          ) : (
            <span className="text-muted-foreground text-sm">
              No filters added
            </span>
          )}
        </div>
      </div>

      {/* Case Sensitive Filters */}
      <div className="space-y-3">
        <Label className="text-base font-medium">
          Case Sensitive Filters
        </Label>
        <p className="text-sm text-muted-foreground">
          Filters that match exactly as typed (e.g., "AMAZON" only matches
          "AMAZON")
        </p>

        <div className="flex space-x-2">
          <Input
            placeholder="Add filter term..."
            value={newCaseSensitive}
            onChange={(e) => setNewCaseSensitive(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addCaseSensitiveFilter();
              }
            }}
          />
          <Button
            type="button"
            onClick={addCaseSensitiveFilter}
            size="sm"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex flex-wrap gap-2 min-h-8 p-3 bg-muted rounded-md">
          {filters.case_sensitive && filters.case_sensitive.length > 0 ? (
            filters.case_sensitive.map((filter, index) => (
              <div
                key={index}
                className="flex items-center space-x-1 bg-secondary text-secondary-foreground px-2 py-1 rounded-md text-sm"
              >
                <span>{filter}</span>
                <Button
                  type="button"
                  onClick={() => removeCaseSensitiveFilter(index)}
                  variant="ghost"
                  size="icon"
                  className="h-5 w-5 hover:bg-secondary-foreground/10"
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            ))
          ) : (
            <span className="text-muted-foreground text-sm">
              No filters added
            </span>
          )}
        </div>
      </div>
    </SettingsDrawer>
  );
}
