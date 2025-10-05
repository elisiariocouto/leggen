import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, X } from "lucide-react";
import { apiClient } from "../lib/api";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
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
import type { NotificationSettings, NotificationFilters } from "../types/api";

interface NotificationFiltersDrawerProps {
  settings: NotificationSettings | undefined;
  trigger?: React.ReactNode;
}

export default function NotificationFiltersDrawer({
  settings,
  trigger,
}: NotificationFiltersDrawerProps) {
  const [open, setOpen] = useState(false);
  const [filters, setFilters] = useState<NotificationFilters>({
    case_insensitive: [],
    case_sensitive: [],
  });
  const [newCaseInsensitive, setNewCaseInsensitive] = useState("");
  const [newCaseSensitive, setNewCaseSensitive] = useState("");

  const queryClient = useQueryClient();

  useEffect(() => {
    if (settings?.filters) {
      setFilters({
        case_insensitive: [...(settings.filters.case_insensitive || [])],
        case_sensitive: [...(settings.filters.case_sensitive || [])],
      });
    }
  }, [settings]);

  const updateMutation = useMutation({
    mutationFn: (updatedFilters: NotificationFilters) =>
      apiClient.updateNotificationSettings({
        ...settings,
        filters: updatedFilters,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notificationSettings"] });
      setOpen(false);
    },
    onError: (error) => {
      console.error("Failed to update notification filters:", error);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate(filters);
  };

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
    <Drawer open={open} onOpenChange={setOpen}>
      <DrawerTrigger asChild>{trigger || <EditButton />}</DrawerTrigger>
      <DrawerContent>
        <div className="mx-auto w-full max-w-2xl">
          <DrawerHeader>
            <DrawerTitle>Notification Filters</DrawerTitle>
            <DrawerDescription>
              Configure which transaction descriptions should trigger
              notifications
            </DrawerDescription>
          </DrawerHeader>

          <form onSubmit={handleSubmit} className="p-4 space-y-6">
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

              <div className="flex flex-wrap gap-2 min-h-[2rem] p-3 bg-muted rounded-md">
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

              <div className="flex flex-wrap gap-2 min-h-[2rem] p-3 bg-muted rounded-md">
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

            <DrawerFooter className="px-0">
              <Button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending ? "Saving..." : "Save Filters"}
              </Button>
              <DrawerClose asChild>
                <Button variant="outline">Cancel</Button>
              </DrawerClose>
            </DrawerFooter>
          </form>
        </div>
      </DrawerContent>
    </Drawer>
  );
}
