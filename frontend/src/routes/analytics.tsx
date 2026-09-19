import { createFileRoute, redirect } from "@tanstack/react-router";
import type { HomeSearch } from "./index";

/**
 * The dashboard used to live here and is now the home page. Saved links
 * and the installed PWA's old shortcut land on "/" with their filters kept.
 */
export const Route = createFileRoute("/analytics")({
  beforeLoad: ({ location }) => {
    throw redirect({
      to: "/",
      search: location.search as HomeSearch,
      replace: true,
    });
  },
});
