import { useEffect, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../lib/api";
import { formatCurrency, formatDate } from "../lib/utils";
import { navigation } from "../lib/navigation";
import { queryKeys } from "../lib/queryKeys";
import { BlurredValue } from "./ui/blurred-value";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "./ui/command";
import type { PaginatedResponse, Transaction } from "../types/api";

/** Below this, a search matches too much to be worth a request. */
const MIN_QUERY_LENGTH = 2;
const RESULT_LIMIT = 5;

export interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");

  // Reopening starts clean rather than on the last search's results. Done
  // in the close handler rather than an effect on `open`, which would be a
  // cascading render.
  const handleOpenChange = (next: boolean) => {
    if (!next) {
      setQuery("");
      setDebouncedQuery("");
    }
    onOpenChange(next);
  };

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 250);
    return () => clearTimeout(timer);
  }, [query]);

  const trimmed = debouncedQuery.trim();
  const isSearching = trimmed.length >= MIN_QUERY_LENGTH;

  const { data: results, isFetching } = useQuery<PaginatedResponse<Transaction>>(
    {
      queryKey: queryKeys.transactionSearch(trimmed),
      queryFn: () =>
        apiClient.getTransactions({
          search: trimmed,
          perPage: RESULT_LIMIT,
          summaryOnly: false,
        }),
      enabled: open && isSearching,
      placeholderData: (previousData) => previousData,
    },
  );

  const transactions = results?.data ?? [];

  const go = (to: string) => {
    handleOpenChange(false);
    navigate({ to });
  };

  // The detail panel is local state inside TransactionsTable, not a route,
  // so a result cannot be deep-linked. Landing on the filtered list puts the
  // row one click from its details.
  const openTransaction = (transaction: Transaction) => {
    handleOpenChange(false);
    navigate({ to: "/", search: { q: transaction.description } });
  };

  return (
    <CommandDialog
      open={open}
      onOpenChange={handleOpenChange}
      // Results come from the API already filtered; cmdk's own fuzzy pass
      // would filter them a second time and hide valid matches.
      shouldFilter={false}
    >
      <CommandInput
        placeholder="Search transactions or jump to a page..."
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        <CommandGroup heading="Go to">
          {navigation.map((item) => (
            <CommandItem
              key={item.to}
              value={item.name}
              onSelect={() => go(item.to)}
            >
              <item.icon className="mr-2 h-4 w-4" />
              {item.name}
            </CommandItem>
          ))}
        </CommandGroup>

        {isSearching && (
          <>
            <CommandSeparator />
            <CommandGroup heading="Transactions">
              {transactions.map((transaction) => (
                <CommandItem
                  key={`${transaction.account_id}-${transaction.transaction_id}`}
                  value={`${transaction.account_id}-${transaction.transaction_id}`}
                  onSelect={() => openTransaction(transaction)}
                >
                  <div className="flex w-full items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate">{transaction.description}</p>
                      <p className="text-xs text-muted-foreground">
                        {transaction.transaction_date
                          ? formatDate(transaction.transaction_date)
                          : "No date"}
                      </p>
                    </div>
                    <BlurredValue>
                      <span
                        className={
                          transaction.transaction_value > 0
                            ? "text-positive shrink-0"
                            : "text-negative shrink-0"
                        }
                      >
                        {formatCurrency(
                          transaction.transaction_value,
                          transaction.transaction_currency,
                        )}
                      </span>
                    </BlurredValue>
                  </div>
                </CommandItem>
              ))}
              {transactions.length === 0 && (
                <div className="px-2 py-3 text-sm text-muted-foreground">
                  {isFetching ? "Searching..." : "No transactions found."}
                </div>
              )}
            </CommandGroup>
          </>
        )}

        {/* Only reachable when the nav list itself matches nothing, which
            cannot happen with filtering off — but cmdk expects the slot. */}
        <CommandEmpty>No results found.</CommandEmpty>
      </CommandList>
    </CommandDialog>
  );
}
