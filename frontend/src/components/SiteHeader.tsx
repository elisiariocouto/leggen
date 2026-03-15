import { useLocation } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../lib/api";
import { ThemeToggle } from "./ui/theme-toggle";
import { BalanceToggle } from "./ui/balance-toggle";
import { Separator } from "./ui/separator";
import { SidebarTrigger } from "./ui/sidebar";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "./ui/tooltip";

const navigation = [
  { name: "Transactions", to: "/" },
  { name: "Analytics", to: "/analytics" },
  { name: "Accounts", to: "/accounts" },
  { name: "Sync", to: "/sync" },
  { name: "Settings", to: "/settings" },
];

export function SiteHeader() {
  const location = useLocation();
  const currentPage =
    navigation.find((item) => item.to === location.pathname)?.name ||
    "Dashboard";

  const {
    data: healthStatus,
    isLoading: healthLoading,
    isError: healthError,
  } = useQuery({
    queryKey: ["health"],
    queryFn: apiClient.getHealth,
    refetchInterval: 30000,
  });

  return (
    <header className="flex h-16 shrink-0 items-center gap-2 border-b transition-[width,height] ease-linear">
      <div className="flex w-full items-center gap-1 px-4 lg:gap-2 lg:px-6">
        <SidebarTrigger className="-ml-1" />
        <Separator
          orientation="vertical"
          className="mx-2 data-[orientation=vertical]:h-4"
        />
        <h1 className="text-lg font-semibold text-card-foreground">
          {currentPage}
        </h1>

        <div className="ml-auto flex items-center space-x-3">
          {/* Version display */}
          <span className="text-xs text-muted-foreground">
            v{healthStatus?.version || "?"}
          </span>

          {/* Connection status */}
          <Tooltip>
            <TooltipTrigger asChild>
              <div
                className={`w-2.5 h-2.5 rounded-full ${
                  healthLoading
                    ? "bg-muted-foreground animate-pulse"
                    : healthError || healthStatus?.status !== "healthy"
                      ? "bg-destructive"
                      : "bg-green-500"
                }`}
                role="img"
                aria-label={
                  healthLoading
                    ? "Checking connection"
                    : healthError || healthStatus?.status !== "healthy"
                      ? "Disconnected"
                      : "Connected"
                }
              />
            </TooltipTrigger>
            <TooltipContent>
              {healthLoading
                ? "Checking..."
                : healthError || healthStatus?.status !== "healthy"
                  ? "Disconnected"
                  : "Connected"}
            </TooltipContent>
          </Tooltip>
          <BalanceToggle />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
