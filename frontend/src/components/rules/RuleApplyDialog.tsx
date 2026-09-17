import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Play } from "lucide-react";
import { toast } from "sonner";

import { apiClient, getApiErrorMessage } from "@/lib/api";
import { invalidateRuleData } from "@/lib/queryKeys";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import type { RuleRunReport } from "@/types/api";

/**
 * Runs the rules over history: a dry run first, so the user sees what would
 * change before anything does.
 */
export default function RuleApplyDialog() {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();

  const dryRun = useMutation<RuleRunReport>({
    mutationFn: () => apiClient.applyCategoryRules(true),
  });
  const apply = useMutation<RuleRunReport>({
    mutationFn: () => apiClient.applyCategoryRules(false),
    onSuccess: (report) => {
      invalidateRuleData(queryClient);
      toast.success(
        `Rules applied: ${report.assigned} categorized, ${report.cleared} cleared.`,
      );
      setOpen(false);
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to apply rules."));
    },
  });

  const handleOpenChange = (isOpen: boolean) => {
    setOpen(isOpen);
    if (isOpen) {
      dryRun.reset();
      dryRun.mutate();
    }
  };

  const report = dryRun.data;
  const nothingToDo = report && report.assigned === 0 && report.cleared === 0;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger
        render={
          <Button variant="outline" size="sm">
            <Play className="mr-1 h-4 w-4" />
            Run rules
          </Button>
        }
      />
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Run rules over all transactions</DialogTitle>
          <DialogDescription>
            Re-evaluates every active rule against transactions without a
            manually chosen category. Manual categories are never changed.
          </DialogDescription>
        </DialogHeader>

        {dryRun.isPending && (
          <p className="text-sm text-muted-foreground">Checking what would change...</p>
        )}
        {dryRun.isError && (
          <p className="text-sm text-destructive">
            {getApiErrorMessage(dryRun.error, "Could not run the rules.")}
          </p>
        )}
        {report && (
          <div className="space-y-3 text-sm">
            <p>
              {report.rules_evaluated} active rule
              {report.rules_evaluated === 1 ? "" : "s"} over{" "}
              {report.transactions_evaluated} transaction
              {report.transactions_evaluated === 1 ? "" : "s"}:{" "}
              <span className="font-medium">{report.assigned}</span> would be
              categorized and{" "}
              <span className="font-medium">{report.cleared}</span> would lose
              a category no rule reproduces any more.
            </p>
            {report.skipped_rules.length > 0 && (
              <div className="rounded-md border border-destructive/40 p-2 text-destructive">
                {report.skipped_rules.length} rule
                {report.skipped_rules.length === 1 ? " does" : "s do"} not
                compile and will be skipped.
              </div>
            )}
            {report.errors.length > 0 && (
              <div className="rounded-md border border-amber-500/40 p-2 text-amber-700 dark:text-amber-400">
                {report.errors.map((e) => (
                  <div key={e.rule_id}>
                    &ldquo;{e.rule_name}&rdquo; failed on {e.count} transaction
                    {e.count === 1 ? "" : "s"}: {e.samples[0]}
                  </div>
                ))}
              </div>
            )}
            {report.changes.length > 0 && (
              <div className="max-h-48 divide-y overflow-y-auto rounded-md border">
                {report.changes.slice(0, 50).map((c) => (
                  <div
                    key={`${c.account_id}-${c.transaction_id}`}
                    className="flex items-center justify-between gap-3 px-3 py-1.5"
                  >
                    <span className="min-w-0 truncate">{c.description}</span>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {c.action === "assign" ? "categorize" : "clear"}
                    </span>
                  </div>
                ))}
                {report.changes.length > 50 && (
                  <p className="p-2 text-center text-xs text-muted-foreground">
                    and {report.changes.length - 50} more
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" size="sm" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button
            size="sm"
            onClick={() => apply.mutate()}
            disabled={!report || nothingToDo || apply.isPending}
          >
            {apply.isPending
              ? "Applying..."
              : nothingToDo
                ? "Nothing to apply"
                : "Apply"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
