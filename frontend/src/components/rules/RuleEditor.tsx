import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Check, ChevronDown, FlaskConical, Search, Tag } from "lucide-react";

import { apiClient, getApiErrorMessage } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";
import { cn, formatCurrency } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { BlurredValue } from "@/components/ui/blurred-value";
import RuleReference from "./RuleReference";
import type {
  Category,
  CategoryRule,
  PaginatedResponse,
  RulePreviewResponse,
  RuleTestResult,
  Transaction,
} from "@/types/api";

export interface RuleDraft {
  name: string;
  description: string;
  category_id: number | null;
  lua_script: string;
  priority: number;
  is_active: boolean;
  exclude_from_stats: boolean | null;
}

const DEFAULT_SCRIPT = 'return contains(tx.merchant, "")';

/**
 * A rule matching one merchant as the analytics page names it. `tx.merchant`
 * is the same normalized label the merchant rankings group by, so the draft
 * matches exactly the rows the reader clicked on.
 */
export function draftForMerchant(merchant: string): RuleDraft {
  const escaped = merchant.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
  return {
    ...draftFromRule(),
    name: merchant,
    lua_script: `return contains(tx.merchant, "${escaped}")`,
  };
}

export function draftFromRule(rule?: CategoryRule): RuleDraft {
  return {
    name: rule?.name ?? "",
    description: rule?.description ?? "",
    category_id: rule?.category_id ?? null,
    lua_script: rule?.lua_script ?? DEFAULT_SCRIPT,
    priority: rule?.priority ?? 100,
    is_active: rule?.is_active ?? true,
    exclude_from_stats: rule?.exclude_from_stats ?? null,
  };
}

function CategoryPicker({
  value,
  onChange,
}: {
  value: number | null;
  onChange: (id: number) => void;
}) {
  const [open, setOpen] = useState(false);
  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: queryKeys.categories,
    queryFn: apiClient.getCategories,
  });
  const selected = categories.find((c) => c.id === value);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger
        render={
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between"
          >
            <span className="flex items-center">
              {selected ? (
                <span
                  className="mr-2 h-3 w-3 shrink-0 rounded-full"
                  style={{ backgroundColor: selected.color }}
                />
              ) : (
                <Tag className="mr-2 h-4 w-4 text-muted-foreground" />
              )}
              {selected?.name ?? "Choose a category"}
            </span>
            <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        }
      />
      <PopoverContent className="w-[240px] p-0" align="start">
        <Command>
          <CommandInput placeholder="Search categories..." className="h-9" />
          <CommandList>
            <CommandEmpty>No categories found.</CommandEmpty>
            <CommandGroup>
              {categories.map((cat) => (
                <CommandItem
                  key={cat.id}
                  value={cat.name}
                  onSelect={() => {
                    onChange(cat.id);
                    setOpen(false);
                  }}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      cat.id === value ? "opacity-100" : "opacity-0",
                    )}
                  />
                  <span
                    className="mr-2 h-3 w-3 shrink-0 rounded-full"
                    style={{ backgroundColor: cat.color }}
                  />
                  {cat.name}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

/** Runs the draft script against one transaction picked by search. */
function TestPanel({ script }: { script: string }) {
  const [search, setSearch] = useState("");
  const [picked, setPicked] = useState<Transaction | null>(null);

  const { data: candidates, isFetching } = useQuery<
    PaginatedResponse<Transaction>
  >({
    queryKey: queryKeys.transactionSearch(`rule-test:${search}`),
    queryFn: () =>
      apiClient.getTransactions({
        search: search || undefined,
        perPage: 8,
        summaryOnly: false,
      }),
  });

  const test = useMutation<RuleTestResult, unknown, Transaction>({
    mutationFn: (transaction) =>
      apiClient.testRuleScript(
        script,
        transaction.account_id,
        transaction.transaction_id,
      ),
  });

  const run = (transaction: Transaction) => {
    setPicked(transaction);
    test.mutate(transaction);
  };

  return (
    <div className="space-y-3">
      <div className="relative">
        <Search className="pointer-events-none absolute top-2.5 left-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Find a transaction to test against..."
          className="pl-8"
        />
      </div>
      <div className="max-h-56 divide-y overflow-y-auto rounded-md border">
        {candidates?.data.length === 0 && !isFetching && (
          <p className="p-3 text-sm text-muted-foreground">
            No transactions match.
          </p>
        )}
        {candidates?.data.map((t) => {
          const isPicked =
            picked?.transaction_id === t.transaction_id &&
            picked?.account_id === t.account_id;
          return (
            <button
              key={`${t.account_id}-${t.transaction_id}`}
              type="button"
              onClick={() => run(t)}
              className={cn(
                "flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm hover:bg-muted/50",
                isPicked && "bg-muted",
              )}
            >
              <span className="min-w-0 truncate">{t.description}</span>
              <span className="shrink-0 tabular-nums text-muted-foreground">
                <BlurredValue>
                  {formatCurrency(t.transaction_value, t.transaction_currency)}
                </BlurredValue>
              </span>
            </button>
          );
        })}
      </div>

      {test.isError && (
        <p className="text-sm text-destructive">
          {getApiErrorMessage(test.error, "The script could not be run.")}
        </p>
      )}
      {test.data && picked && (
        <div className="rounded-md border p-3 text-sm">
          <div className="flex items-center justify-between">
            <span className="truncate text-muted-foreground">
              {picked.description}
            </span>
            {test.data.error ? (
              <span className="font-medium text-destructive">Error</span>
            ) : test.data.matched ? (
              <span className="font-medium text-positive">Matches</span>
            ) : (
              <span className="font-medium text-muted-foreground">
                No match
              </span>
            )}
          </div>
          {test.data.error && (
            <pre className="mt-2 whitespace-pre-wrap font-mono text-xs text-destructive">
              {test.data.error}
            </pre>
          )}
          {(test.data.logs ?? []).length > 0 && (
            <pre className="mt-2 max-h-40 overflow-auto rounded bg-muted p-2 font-mono text-xs">
              {(test.data.logs ?? []).join("\n")}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}

/** Lists everything the draft script matches, so its reach can be judged. */
function PreviewPanel({ script }: { script: string }) {
  const preview = useMutation<RulePreviewResponse>({
    mutationFn: () => apiClient.previewRuleScript(script, 1, 100),
  });

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">
          Runs the script over every transaction. Manually categorized ones
          are shown but never changed.
        </p>
        <Button
          size="sm"
          variant="outline"
          onClick={() => preview.mutate()}
          disabled={preview.isPending}
        >
          <FlaskConical className="mr-1 h-4 w-4" />
          {preview.isPending ? "Running..." : "Preview"}
        </Button>
      </div>
      {preview.isError && (
        <p className="text-sm text-destructive">
          {getApiErrorMessage(preview.error, "The script could not be run.")}
        </p>
      )}
      {preview.data && (
        <>
          <p className="text-sm">
            <span className="font-medium">{preview.data.total}</span> of{" "}
            {preview.data.evaluated} transactions match
            {preview.data.errors > 0 && (
              <span className="text-destructive">
                {" "}
                · {preview.data.errors} raised an error
              </span>
            )}
          </p>
          {(preview.data.error_samples ?? []).length > 0 && (
            <pre className="whitespace-pre-wrap rounded bg-muted p-2 font-mono text-xs text-destructive">
              {(preview.data.error_samples ?? []).join("\n")}
            </pre>
          )}
          <div className="max-h-64 divide-y overflow-y-auto rounded-md border">
            {preview.data.data.map((m) => (
              <div
                key={`${m.account_id}-${m.transaction_id}`}
                className="flex items-center justify-between gap-3 px-3 py-2 text-sm"
              >
                <div className="min-w-0">
                  <div className="truncate">{m.description}</div>
                  <div className="text-xs text-muted-foreground">
                    {m.date}
                    {m.category_name && (
                      <>
                        {" · "}
                        {m.category_name}
                        {m.manual && " (manual, kept)"}
                      </>
                    )}
                  </div>
                </div>
                <span className="shrink-0 tabular-nums text-muted-foreground">
                  <BlurredValue>
                    {m.amount != null && m.currency
                      ? formatCurrency(m.amount, m.currency)
                      : "—"}
                  </BlurredValue>
                </span>
              </div>
            ))}
            {preview.data.total > preview.data.data.length && (
              <p className="p-2 text-center text-xs text-muted-foreground">
                Showing the first {preview.data.data.length}.
              </p>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default function RuleEditor({
  draft,
  onChange,
  onSave,
  onCancel,
  isSaving,
  isNew,
}: {
  draft: RuleDraft;
  onChange: (draft: RuleDraft) => void;
  onSave: () => void;
  onCancel: () => void;
  isSaving: boolean;
  isNew: boolean;
}) {
  const set = <K extends keyof RuleDraft>(key: K, value: RuleDraft[K]) =>
    onChange({ ...draft, [key]: value });
  const canSave =
    draft.name.trim() !== "" &&
    draft.category_id !== null &&
    draft.lua_script.trim() !== "";

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
      <div className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="rule-name">Name</Label>
            <Input
              id="rule-name"
              value={draft.name}
              onChange={(e) => set("name", e.target.value)}
              placeholder="Supermarkets"
            />
          </div>
          <div className="space-y-2">
            <Label>Category</Label>
            <CategoryPicker
              value={draft.category_id}
              onChange={(id) => set("category_id", id)}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="rule-description">Description</Label>
          <Input
            id="rule-description"
            value={draft.description}
            onChange={(e) => set("description", e.target.value)}
            placeholder="What this rule is for (optional)"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="rule-script">Script</Label>
          <Textarea
            id="rule-script"
            value={draft.lua_script}
            onChange={(e) => set("lua_script", e.target.value)}
            spellCheck={false}
            className="min-h-40 font-mono text-xs"
          />
          <p className="text-xs text-muted-foreground">
            The body of <code>function(tx) ... end</code>. Return{" "}
            <code>true</code> to apply the rule.
          </p>
        </div>

        <Tabs defaultValue="test">
          <TabsList>
            <TabsTrigger value="test">Test</TabsTrigger>
            <TabsTrigger value="preview">Preview</TabsTrigger>
            <TabsTrigger value="options">Options</TabsTrigger>
          </TabsList>
          <TabsContent value="test" className="pt-3">
            <TestPanel script={draft.lua_script} />
          </TabsContent>
          <TabsContent value="preview" className="pt-3">
            <PreviewPanel script={draft.lua_script} />
          </TabsContent>
          <TabsContent value="options" className="space-y-4 pt-3">
            <div className="space-y-2">
              <Label htmlFor="rule-priority">Priority</Label>
              <Input
                id="rule-priority"
                type="number"
                min={0}
                value={draft.priority}
                onChange={(e) => set("priority", Number(e.target.value) || 0)}
                className="w-32"
              />
              <p className="text-xs text-muted-foreground">
                Rules run in ascending order; the first match wins.
              </p>
            </div>
            <div className="flex items-center justify-between gap-4">
              <div>
                <Label htmlFor="rule-active">Active</Label>
                <p className="text-xs text-muted-foreground">
                  Inactive rules are kept but never run.
                </p>
              </div>
              <Switch
                id="rule-active"
                checked={draft.is_active}
                onCheckedChange={(checked) => set("is_active", checked)}
              />
            </div>
            <div className="flex items-center justify-between gap-4">
              <div>
                <Label htmlFor="rule-exclude">Exclude matches from statistics</Label>
                <p className="text-xs text-muted-foreground">
                  {draft.exclude_from_stats === null
                    ? "Following the category's own setting."
                    : draft.exclude_from_stats
                      ? "Matched transactions stay out of the totals."
                      : "Matched transactions count even if the category is excluded."}
                  {draft.exclude_from_stats !== null && (
                    <>
                      {" "}
                      <button
                        type="button"
                        className="text-primary hover:underline"
                        onClick={() => set("exclude_from_stats", null)}
                      >
                        Reset
                      </button>
                    </>
                  )}
                </p>
              </div>
              <Switch
                id="rule-exclude"
                checked={draft.exclude_from_stats === true}
                onCheckedChange={(checked) => set("exclude_from_stats", checked)}
              />
            </div>
          </TabsContent>
        </Tabs>

        <div className="flex justify-end gap-2">
          <Button variant="outline" size="sm" onClick={onCancel}>
            Cancel
          </Button>
          <Button size="sm" onClick={onSave} disabled={!canSave || isSaving}>
            {isSaving ? "Saving..." : isNew ? "Create" : "Save"}
          </Button>
        </div>
      </div>

      <aside className="max-h-[70vh] overflow-y-auto rounded-md border p-4">
        <RuleReference onUseExample={(script) => set("lua_script", script)} />
      </aside>
    </div>
  );
}
