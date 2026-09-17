import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { EyeOff, Pencil, Plus, Trash2, WandSparkles } from "lucide-react";
import { toast } from "sonner";

import { apiClient, getApiErrorMessage } from "../lib/api";
import { invalidateRuleData, queryKeys } from "../lib/queryKeys";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Button } from "./ui/button";
import { Switch } from "./ui/switch";
import { Skeleton } from "./ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
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
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "./ui/empty";
import RuleEditor, { draftFromRule, type RuleDraft } from "./rules/RuleEditor";
import RuleApplyDialog from "./rules/RuleApplyDialog";
import type { Category, CategoryRule } from "../types/api";

/**
 * The category rules page: the rules in the order they run, an editor with
 * test and preview built in, and the button that runs them over history.
 */
export default function CategoryRules() {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<CategoryRule | "new" | null>(null);
  const [draft, setDraft] = useState<RuleDraft>(draftFromRule());
  const [deleteTarget, setDeleteTarget] = useState<CategoryRule | null>(null);

  const { data: rules, isLoading } = useQuery<CategoryRule[]>({
    queryKey: queryKeys.categoryRules,
    queryFn: apiClient.getCategoryRules,
  });
  const { data: categories } = useQuery<Category[]>({
    queryKey: queryKeys.categories,
    queryFn: apiClient.getCategories,
  });
  const categoryById = new Map((categories ?? []).map((c) => [c.id, c]));

  const openEditor = (rule: CategoryRule | "new") => {
    setDraft(draftFromRule(rule === "new" ? undefined : rule));
    setEditing(rule);
  };

  const save = useMutation({
    mutationFn: () => {
      const body = {
        name: draft.name.trim(),
        description: draft.description.trim() || null,
        category_id: draft.category_id as number,
        lua_script: draft.lua_script,
        priority: draft.priority,
        is_active: draft.is_active,
        exclude_from_stats: draft.exclude_from_stats,
      };
      return editing === "new" || editing === null
        ? apiClient.createCategoryRule(body)
        : apiClient.updateCategoryRule(editing.id, body);
    },
    onSuccess: () => {
      invalidateRuleData(queryClient);
      setEditing(null);
      toast.success(
        editing === "new"
          ? "Rule created. Run rules to apply it to existing transactions."
          : "Rule saved. Run rules to re-apply it to existing transactions.",
      );
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to save rule."));
    },
  });

  const toggleActive = useMutation({
    mutationFn: ({ id, active }: { id: number; active: boolean }) =>
      apiClient.updateCategoryRule(id, { is_active: active }),
    onSuccess: () => invalidateRuleData(queryClient),
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to update rule."));
    },
  });

  const remove = useMutation({
    mutationFn: (id: number) => apiClient.deleteCategoryRule(id),
    onSuccess: () => {
      invalidateRuleData(queryClient);
      setDeleteTarget(null);
      toast.success("Rule deleted.");
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to delete rule."));
    },
  });

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <CardTitle className="flex items-center space-x-2">
              <WandSparkles className="h-5 w-5 text-primary" />
              <span>Category rules</span>
            </CardTitle>
            <div className="flex items-center gap-2">
              <RuleApplyDialog />
              <Button size="sm" onClick={() => openEditor("new")}>
                <Plus className="mr-1 h-4 w-4" />
                New rule
              </Button>
            </div>
          </div>
          <CardDescription>
            Small scripts that categorize transactions as they arrive. Rules run
            in this order and the first one that matches wins; a category you
            pick by hand is never overridden.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : rules && rules.length > 0 ? (
            <div className="divide-y">
              {rules.map((rule) => {
                const category = categoryById.get(rule.category_id);
                return (
                  <div
                    key={rule.id}
                    className="flex items-center gap-3 py-2.5 first:pt-0 last:pb-0"
                  >
                    <Switch
                      size="sm"
                      checked={rule.is_active}
                      aria-label={`${rule.name} active`}
                      onCheckedChange={(checked) =>
                        toggleActive.mutate({ id: rule.id, active: checked })
                      }
                    />
                    <span className="w-10 shrink-0 text-right font-mono text-xs text-muted-foreground tabular-nums">
                      {rule.priority}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          className={`text-sm font-medium ${
                            rule.is_active ? "" : "text-muted-foreground"
                          }`}
                        >
                          {rule.name}
                        </span>
                        {rule.is_default && (
                          <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
                            built in
                          </span>
                        )}
                        {rule.exclude_from_stats === true && (
                          <span className="flex items-center gap-0.5 rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
                            <EyeOff className="h-2.5 w-2.5" />
                            excludes from stats
                          </span>
                        )}
                      </div>
                      {rule.description && (
                        <p className="truncate text-xs text-muted-foreground">
                          {rule.description}
                        </p>
                      )}
                    </div>
                    <span
                      className="hidden shrink-0 items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium sm:inline-flex"
                      style={{
                        backgroundColor: `${category?.color ?? "#6b7280"}20`,
                        color: category?.color ?? "#6b7280",
                      }}
                    >
                      <span
                        className="h-2 w-2 rounded-full"
                        style={{ backgroundColor: category?.color ?? "#6b7280" }}
                      />
                      {rule.category_name ?? category?.name ?? "—"}
                    </span>
                    <div className="flex shrink-0 items-center">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0"
                        aria-label={`Edit ${rule.name}`}
                        onClick={() => openEditor(rule)}
                      >
                        <Pencil className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 text-destructive hover:text-destructive"
                        aria-label={`Delete ${rule.name}`}
                        onClick={() => setDeleteTarget(rule)}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <Empty className="border-0 py-10">
              <EmptyHeader>
                <EmptyMedia variant="icon">
                  <WandSparkles />
                </EmptyMedia>
                <EmptyTitle>No rules yet</EmptyTitle>
                <EmptyDescription>
                  Create one to categorize transactions automatically.
                </EmptyDescription>
              </EmptyHeader>
            </Empty>
          )}
        </CardContent>
      </Card>

      <Dialog open={editing !== null} onOpenChange={(open) => !open && setEditing(null)}>
        <DialogContent className="max-h-[92dvh] overflow-y-auto sm:max-w-5xl">
          <DialogHeader>
            <DialogTitle>{editing === "new" ? "New rule" : "Edit rule"}</DialogTitle>
            <DialogDescription>
              Write the script, test it against a transaction, preview what it
              matches, then save.
            </DialogDescription>
          </DialogHeader>
          {editing !== null && (
            <RuleEditor
              draft={draft}
              onChange={setDraft}
              onSave={() => save.mutate()}
              onCancel={() => setEditing(null)}
              isSaving={save.isPending}
              isNew={editing === "new"}
            />
          )}
        </DialogContent>
      </Dialog>

      <AlertDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete rule</AlertDialogTitle>
            <AlertDialogDescription>
              Delete &ldquo;{deleteTarget?.name}&rdquo;? Categories this rule
              assigned are removed from their transactions; categories chosen
              by hand stay.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteTarget && remove.mutate(deleteTarget.id)}
              disabled={remove.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {remove.isPending ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
