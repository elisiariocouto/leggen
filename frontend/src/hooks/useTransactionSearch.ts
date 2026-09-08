import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearch } from "@tanstack/react-router";

import { asNonNegativeNumber } from "@/lib/searchParams";
import type { SortDirection, TransactionSortField } from "@/lib/searchParams";
import type { FilterState } from "@/components/filters";
import type { TransactionSearch } from "@/routes/index";

/** Which URL param backs each filter field. */
const PARAM_FOR: Record<keyof FilterState, keyof TransactionSearch> = {
  searchTerm: "q",
  selectedAccount: "account",
  selectedCategory: "category",
  selectedStatus: "status",
  startDate: "from",
  endDate: "to",
  minAmount: "minAmount",
  maxAmount: "maxAmount",
};

const DEFAULT_PER_PAGE = 50;
const DEFAULT_SORT: TransactionSortField = "date";
const DEFAULT_DIR: SortDirection = "desc";

/**
 * The transaction list's view state, which lives in the URL.
 *
 * Filters and pagination are search params so a filtered view survives a
 * refresh, can be shared, and steps back through history. This hook owns all
 * of that plumbing — the param mapping, the search-input debounce, and the
 * page-overflow guard — leaving the component to render.
 */
export function useTransactionSearch() {
  const search = useSearch({ from: "/" });
  const navigate = useNavigate({ from: "/" });

  const filterState: FilterState = useMemo(
    () => ({
      searchTerm: search.q ?? "",
      selectedAccount: search.account ?? "",
      selectedCategory: search.category ?? "",
      selectedStatus: search.status ?? "",
      startDate: search.from ?? "",
      endDate: search.to ?? "",
      minAmount: search.minAmount?.toString() ?? "",
      maxAmount: search.maxAmount?.toString() ?? "",
    }),
    [
      search.q,
      search.account,
      search.category,
      search.status,
      search.from,
      search.to,
      search.minAmount,
      search.maxAmount,
    ],
  );

  // Sort is a view preference rather than a filter: it has no chip, and it
  // survives Clear All. Absent params mean the default ordering.
  const sortBy = search.sort ?? DEFAULT_SORT;
  const sortOrder = search.dir ?? DEFAULT_DIR;

  const currentPage = search.page ?? 1;
  const perPage = search.perPage ?? DEFAULT_PER_PAGE;

  // What is being typed, held locally so keystrokes are not throttled by
  // navigation. Stored alongside the URL value it was typed against: when
  // the URL moves on its own (a back step, Clear All), the draft no longer
  // matches and the URL wins, with no effect needed to resync.
  const urlSearch = search.q ?? "";
  const [draft, setDraft] = useState({ value: urlSearch, from: urlSearch });
  const searchInput = draft.from === urlSearch ? draft.value : urlSearch;
  const setSearchInput = (value: string) => setDraft({ value, from: urlSearch });
  const debouncedSearchTerm = urlSearch;

  // Changing a filter always returns to page 1 — the old page number rarely
  // exists in the new result set. Done in the same navigation as the filter
  // itself, so only one request goes out.
  const handleFilterChange = (key: keyof FilterState, value: string) => {
    if (key === "searchTerm") setSearchInput(value);
    // The amount bounds are numbers in the URL schema; everything else is a
    // string. An unparseable or negative entry drops the bound rather than
    // writing a value validateSearch would reject on the next read.
    const isAmount = key === "minAmount" || key === "maxAmount";
    const nextValue = isAmount ? asNonNegativeNumber(value) : value || undefined;
    navigate({
      search: (prev: TransactionSearch) => ({
        ...prev,
        [PARAM_FOR[key]]: nextValue,
        page: undefined,
      }),
      replace: key === "searchTerm" || isAmount,
    });
  };

  const handleClearFilters = () => {
    setSearchInput("");
    // Sort and page size are view preferences, not filters, so they survive.
    navigate({
      search: (prev: TransactionSearch) => ({
        perPage: prev.perPage,
        sort: prev.sort,
        dir: prev.dir,
      }),
    });
  };

  const handleSortChange = (
    nextSort: TransactionSortField,
    nextDir: SortDirection,
  ) => {
    navigate({
      search: (prev: TransactionSearch) => ({
        ...prev,
        // Omit the defaults so a plain "/" stays the canonical URL.
        sort: nextSort === DEFAULT_SORT ? undefined : nextSort,
        dir: nextDir === DEFAULT_DIR ? undefined : nextDir,
        page: undefined,
      }),
    });
  };

  // Clicking the active column flips direction; a new column starts
  // descending, which is the useful default for both dates and amounts.
  const handleSortColumn = (column: TransactionSortField) => {
    if (column === sortBy) {
      handleSortChange(column, sortOrder === "asc" ? "desc" : "asc");
    } else {
      handleSortChange(column, "desc");
    }
  };

  const setCurrentPage = (page: number) => {
    navigate({
      search: (prev: TransactionSearch) => ({
        ...prev,
        page: page > 1 ? page : undefined,
      }),
    });
  };

  const setPerPage = (size: number) => {
    navigate({
      search: (prev: TransactionSearch) => ({
        ...prev,
        perPage: size === DEFAULT_PER_PAGE ? undefined : size,
        page: undefined,
      }),
    });
  };

  // Push the typed term into the URL once typing settles.
  useEffect(() => {
    if (searchInput === (search.q ?? "")) return;
    const timer = setTimeout(() => {
      handleFilterChange("searchTerm", searchInput);
    }, 300);
    return () => clearTimeout(timer);
    // handleFilterChange is stable enough for this effect's purpose; it only
    // closes over navigate, which TanStack keeps referentially stable.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchInput, search.q]);

  // True while the typed term has not yet reached the URL and the query.
  const isSearchLoading = searchInput !== debouncedSearchTerm;

  // The filter bar shows what is being typed; everything else reflects the URL.
  const displayedFilterState: FilterState = useMemo(
    () => ({ ...filterState, searchTerm: searchInput }),
    [filterState, searchInput],
  );

  const hasActiveFilters = Boolean(
    filterState.searchTerm ||
      filterState.selectedAccount ||
      filterState.selectedCategory ||
      filterState.selectedStatus ||
      filterState.startDate ||
      filterState.endDate,
  );

  return {
    search,
    filterState,
    displayedFilterState,
    hasActiveFilters,
    isSearchLoading,
    debouncedSearchTerm,
    sortBy,
    sortOrder,
    currentPage,
    perPage,
    handleFilterChange,
    handleClearFilters,
    handleSortChange,
    handleSortColumn,
    setCurrentPage,
    setPerPage,
  };
}

/**
 * Send a deep link that points past the end of the result set back to page 1,
 * rather than showing an empty table.
 *
 * Filter changes reset the page in `handleFilterChange`, so this only catches
 * the deep-link case. Kept separate from `useTransactionSearch` because it
 * needs the page count, which only arrives with the response.
 */
export function usePageClamp(
  currentPage: number,
  totalPages: number | undefined,
) {
  const navigate = useNavigate({ from: "/" });
  useEffect(() => {
    if (totalPages === undefined || currentPage === 1) return;
    if (currentPage > totalPages) {
      navigate({
        search: (prev: TransactionSearch) => ({ ...prev, page: undefined }),
      });
    }
  }, [currentPage, totalPages, navigate]);
}
