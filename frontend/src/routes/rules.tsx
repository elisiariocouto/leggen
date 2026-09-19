import { createFileRoute, redirect } from "@tanstack/react-router";
import type { CategoriesSearch } from "./categories";

/**
 * The rules page grew category management and became "Categories". Saved
 * links, including the `?merchant=` hand-off, land there with their search
 * kept.
 */
export const Route = createFileRoute("/rules")({
  beforeLoad: ({ location }) => {
    throw redirect({
      to: "/categories",
      search: location.search as CategoriesSearch,
      replace: true,
    });
  },
});
