import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Tag, Sparkles, X, Check } from "lucide-react";
import { apiClient } from "../lib/api";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "./ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "./ui/command";
import { Checkbox } from "./ui/checkbox";
import { toast } from "sonner";
import type { Category, CategorySuggestion } from "../types/api";

interface CategoryBadgeProps {
  accountId: string;
  transactionId: string;
  categoryId?: number;
  categoryName?: string;
  categoryColor?: string;
  description?: string;
}

export default function CategoryBadge({
  accountId,
  transactionId,
  categoryId,
  categoryName,
  categoryColor,
  description,
}: CategoryBadgeProps) {
  const [open, setOpen] = useState(false);
  const [applyToAll, setApplyToAll] = useState(false);
  const queryClient = useQueryClient();

  const { data: categories } = useQuery<Category[]>({
    queryKey: ["categories"],
    queryFn: apiClient.getCategories,
  });

  const { data: suggestions } = useQuery<CategorySuggestion[]>({
    queryKey: ["category-suggestions", accountId, transactionId],
    queryFn: () => apiClient.getCategorySuggestions(accountId, transactionId),
    enabled: open && !categoryId,
  });

  const assignMutation = useMutation({
    mutationFn: (catId: number) =>
      apiClient.assignCategory(accountId, transactionId, catId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({
        queryKey: ["category-suggestions", accountId, transactionId],
      });
      setOpen(false);
    },
  });

  const bulkAssignMutation = useMutation({
    mutationFn: (catId: number) =>
      apiClient.bulkAssignCategoryByDescription(catId, description || ""),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      toast.success(
        `Category applied to ${data.updated_count} transaction${data.updated_count !== 1 ? "s" : ""}.`,
      );
      setOpen(false);
    },
  });

  const removeMutation = useMutation({
    mutationFn: () => apiClient.removeCategory(accountId, transactionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      setOpen(false);
    },
  });

  const bulkRemoveMutation = useMutation({
    mutationFn: () =>
      apiClient.bulkRemoveCategoryByDescription(description || ""),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      toast.success(
        `Category removed from ${data.removed_count} transaction${data.removed_count !== 1 ? "s" : ""}.`,
      );
      setOpen(false);
    },
  });

  const handleAssign = (catId: number) => {
    if (applyToAll && description) {
      bulkAssignMutation.mutate(catId);
    } else {
      assignMutation.mutate(catId);
    }
  };

  const handleRemove = () => {
    if (applyToAll && description) {
      bulkRemoveMutation.mutate();
    } else {
      removeMutation.mutate();
    }
  };

  const handleOpenChange = (isOpen: boolean) => {
    setOpen(isOpen);
    if (!isOpen) {
      setApplyToAll(false);
    }
  };

  const confidenceBadge = (confidence: string) => {
    const colors: Record<string, string> = {
      high: "text-green-600",
      medium: "text-yellow-600",
      low: "text-muted-foreground",
    };
    return <span className={`text-[10px] ${colors[confidence] || ""}`}>{confidence}</span>;
  };

  const truncatedDescription =
    description && description.length > 30
      ? description.slice(0, 30) + "..."
      : description;

  const color = categoryColor || "#6b7280";
  const isPending =
    assignMutation.isPending ||
    bulkAssignMutation.isPending ||
    removeMutation.isPending ||
    bulkRemoveMutation.isPending;

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        {categoryName ? (
          <button
            className="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium transition-colors hover:opacity-80 cursor-pointer border-0"
            style={{
              backgroundColor: `${color}20`,
              color: color,
            }}
          >
            <span
              className="h-2 w-2 rounded-full flex-shrink-0"
              style={{ backgroundColor: color }}
            />
            {categoryName}
          </button>
        ) : (
          <button className="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors cursor-pointer border border-dashed border-muted-foreground/30">
            <Tag className="h-3 w-3" />
            <span>Categorize</span>
          </button>
        )}
      </PopoverTrigger>
      <PopoverContent className="w-56 p-0" align="start">
        <Command>
          <CommandInput placeholder="Search categories..." />

          {/* Apply to all checkbox */}
          {description && (
            <div className="flex items-center gap-2 px-3 py-2 border-b">
              <Checkbox
                id={`apply-all-${transactionId}`}
                checked={applyToAll}
                onCheckedChange={(checked) => setApplyToAll(checked === true)}
              />
              <label
                htmlFor={`apply-all-${transactionId}`}
                className="text-xs text-muted-foreground cursor-pointer select-none"
                title={description}
              >
                Apply to all &ldquo;{truncatedDescription}&rdquo; transactions
              </label>
            </div>
          )}

          <CommandList>
            <CommandEmpty>No categories found.</CommandEmpty>

            {/* Suggestions section */}
            {suggestions && suggestions.length > 0 && (
              <>
                <CommandGroup heading="Suggestions">
                  {suggestions.map((s) => (
                    <CommandItem
                      key={`suggestion-${s.category.id}`}
                      value={`suggestion-${s.category.name}`}
                      onSelect={() => handleAssign(s.category.id)}
                      disabled={isPending}
                      className="cursor-pointer"
                    >
                      <div className="flex items-center gap-2 flex-1">
                        <Sparkles className="h-3 w-3 text-yellow-500 flex-shrink-0" />
                        <span
                          className="h-2.5 w-2.5 rounded-full flex-shrink-0"
                          style={{ backgroundColor: s.category.color }}
                        />
                        <span className="flex-1">{s.category.name}</span>
                        {confidenceBadge(s.confidence)}
                      </div>
                    </CommandItem>
                  ))}
                </CommandGroup>
                <CommandSeparator />
              </>
            )}

            {/* All categories */}
            <CommandGroup heading="Categories">
              {categories?.map((cat) => (
                <CommandItem
                  key={cat.id}
                  value={cat.name}
                  onSelect={() => handleAssign(cat.id)}
                  disabled={isPending}
                  className="cursor-pointer"
                >
                  <div className="flex items-center gap-2 flex-1">
                    <span
                      className="h-2.5 w-2.5 rounded-full flex-shrink-0"
                      style={{ backgroundColor: cat.color }}
                    />
                    <span className="flex-1">{cat.name}</span>
                    {cat.id === categoryId && (
                      <Check className="h-3 w-3 text-primary" />
                    )}
                  </div>
                </CommandItem>
              ))}
            </CommandGroup>

            {/* Remove category option */}
            {categoryId && (
              <>
                <CommandSeparator />
                <CommandGroup>
                  <CommandItem
                    onSelect={() => handleRemove()}
                    disabled={isPending}
                    className="cursor-pointer text-destructive"
                    value="remove-category"
                  >
                    <X className="h-3 w-3" />
                    <span>Remove category</span>
                  </CommandItem>
                </CommandGroup>
              </>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
