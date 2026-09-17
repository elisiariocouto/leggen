import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { apiClient, getApiErrorMessage } from "@/lib/api";
import { invalidateCategorizedData } from "@/lib/queryKeys";
import { useStatsExclusion } from "@/hooks/useStatsExclusion";
import { Switch } from "./ui/switch";
import { Button } from "./ui/button";
import type { Transaction } from "@/types/api";

/**
 * Switch for a transaction's statistics override.
 *
 * Shows the effective state — what the totals do with this transaction —
 * not the raw override, since that is the question the reader has. Flipping
 * it always writes an explicit value; "Reset" clears it so the category's
 * flag applies again, and only appears while an override exists.
 */
export default function StatsExclusionToggle({
  transaction,
}: {
  transaction: Transaction;
}) {
  const queryClient = useQueryClient();
  const { excluded, overridden, categoryExcluded, hasCategory } =
    useStatsExclusion(transaction);

  const mutation = useMutation({
    mutationFn: (value: boolean | null) =>
      apiClient.updateTransaction(
        transaction.account_id,
        transaction.transaction_id,
        { exclude_from_stats: value },
      ),
    onSuccess: () => invalidateCategorizedData(queryClient),
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to update transaction."));
    },
  });

  const switchId = `exclude-stats-${transaction.transaction_id}`;

  return (
    <div className="flex items-start justify-between gap-4">
      <div className="min-w-0">
        <label htmlFor={switchId} className="text-sm text-muted-foreground">
          Exclude from statistics
        </label>
        <p className="mt-0.5 text-xs text-muted-foreground/70">
          {overridden ? (
            <>
              Overrides the category
              {hasCategory && (
                <>
                  , which is{" "}
                  {categoryExcluded ? "excluded" : "included"}
                </>
              )}
              .{" "}
              <Button
                variant="link"
                size="sm"
                className="h-auto p-0 text-xs"
                disabled={mutation.isPending}
                onClick={() => mutation.mutate(null)}
              >
                Reset
              </Button>
            </>
          ) : hasCategory ? (
            "Follows the category."
          ) : (
            "Counted in totals unless excluded."
          )}
        </p>
      </div>
      <Switch
        id={switchId}
        checked={excluded}
        disabled={mutation.isPending}
        onCheckedChange={(checked) => mutation.mutate(checked)}
        aria-label="Exclude from statistics"
      />
    </div>
  );
}
