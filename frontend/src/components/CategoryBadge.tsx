import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Tag, X, Check, WandSparkles } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { apiClient, getApiErrorMessage } from "../lib/api";
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
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "./ui/tooltip";
import type { Category, CategoryRule } from "../types/api";
import {
  invalidateCategorizedData,
  queryKeys,
} from "../lib/queryKeys";

interface CategoryBadgeProps {
  accountId: string;
  transactionId: string;
  categoryId?: number | null;
  categoryName?: string | null;
  categoryColor?: string | null;
  categorySource?: string | null;
  categoryRuleId?: number | null;
  description?: string;
}

/**
 * Wand beside a category a rule assigned, naming the rule on hover. Rule
 * names are read from the rules query the Rules page already caches.
 */
function RuleProvenance({ ruleId }: { ruleId: number | null | undefined }) {
  const { data: rules } = useQuery<CategoryRule[]>({
    queryKey: queryKeys.categoryRules,
    queryFn: apiClient.getCategoryRules,
    staleTime: 60_000,
  });
  const rule = rules?.find((r) => r.id === ruleId);
  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <Link
            to="/rules"
            className="inline-flex"
            aria-label="Assigned by a rule"
            onClick={(event) => event.stopPropagation()}
          />
        }
      >
        <WandSparkles className="h-3 w-3 opacity-70" />
      </TooltipTrigger>
      <TooltipContent>
        {rule ? `Assigned by rule “${rule.name}”` : "Assigned by a rule"}
      </TooltipContent>
    </Tooltip>
  );
}

export default function CategoryBadge({
  accountId,
  transactionId,
  categoryId,
  categoryName,
  categoryColor,
  categorySource,
  categoryRuleId,
  description,
}: CategoryBadgeProps) {
  const [open, setOpen] = useState(false);
  const [applyToAll, setApplyToAll] = useState(false);
  const queryClient = useQueryClient();

  const { data: categories } = useQuery<Category[]>({
    queryKey: queryKeys.categories,
    queryFn: apiClient.getCategories,
  });

  const assignMutation = useMutation({
    mutationFn: (catId: number) =>
      apiClient.assignCategory(accountId, transactionId, catId),
    onSuccess: () => {
      invalidateCategorizedData(queryClient);
      setOpen(false);
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to assign category."));
    },
  });

  const bulkAssignMutation = useMutation({
    mutationFn: (catId: number) =>
      apiClient.bulkAssignCategoryByDescription(catId, description || ""),
    onSuccess: (data) => {
      invalidateCategorizedData(queryClient);
      toast.success(
        `Category applied to ${data.updated_count} transaction${data.updated_count !== 1 ? "s" : ""}.`,
      );
      setOpen(false);
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to assign category."));
    },
  });

  const removeMutation = useMutation({
    mutationFn: () => apiClient.removeCategory(accountId, transactionId),
    onSuccess: () => {
      invalidateCategorizedData(queryClient);
      setOpen(false);
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to remove category."));
    },
  });

  const bulkRemoveMutation = useMutation({
    mutationFn: () =>
      apiClient.bulkRemoveCategoryByDescription(description || ""),
    onSuccess: (data) => {
      invalidateCategorizedData(queryClient);
      toast.success(
        `Category removed from ${data.removed_count} transaction${data.removed_count !== 1 ? "s" : ""}.`,
      );
      setOpen(false);
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to remove category."));
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
    <span className="inline-flex items-center gap-1">
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger
        render={
          categoryName ? (
            <button
              className="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium transition-colors hover:opacity-80 cursor-pointer border-0"
              style={{
                backgroundColor: `${color}20`,
                color: color,
              }}
            >
              <span
                className="h-2 w-2 rounded-full shrink-0"
                style={{ backgroundColor: color }}
              />
              {categoryName}
            </button>
          ) : (
            <button className="inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors cursor-pointer border border-dashed border-muted-foreground/40">
              <Tag className="h-3.5 w-3.5" />
              <span>Categorize</span>
            </button>
          )
        }
      />
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
                      className="h-2.5 w-2.5 rounded-full shrink-0"
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
    {categoryName && categorySource === "rule" && (
      <span style={{ color }}>
        <RuleProvenance ruleId={categoryRuleId} />
      </span>
    )}
    </span>
  );
}
