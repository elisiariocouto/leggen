import { useLocation } from "@tanstack/react-router";
import { Activity, Wifi, WifiOff } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../lib/api";
import { ThemeToggle } from "./ui/theme-toggle";
import { BalanceToggle } from "./ui/balance-toggle";
import { Separator } from "./ui/separator";
import { SidebarTrigger } from "./ui/sidebar";

const navigation = [
  { name: "Overview", to: "/" },
  { name: "Transactions", to: "/transactions" },
  { name: "Analytics", to: "/analytics" },
  { name: "System", to: "/system" },
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
          <div className="flex items-center space-x-1">
            {healthLoading ? (
              <span className="text-xs text-muted-foreground">v...</span>
            ) : healthError || !healthStatus ? (
              <span className="text-xs text-muted-foreground">v?</span>
            ) : (
              <span className="text-xs text-muted-foreground">
                v{healthStatus.version || "?"}
              </span>
            )}
          </div>

          {/* Connection status */}
          <div className="flex items-center space-x-1">
            {healthLoading ? (
              <>
                <Activity className="h-4 w-4 text-muted-foreground animate-pulse" />
                <span className="text-sm text-muted-foreground">
                  Checking...
                </span>
              </>
            ) : healthError || healthStatus?.status !== "healthy" ? (
              <>
                <WifiOff className="h-4 w-4 text-destructive" />
                <span className="text-sm text-destructive">Disconnected</span>
              </>
            ) : (
              <>
                <Wifi className="h-4 w-4 text-green-500" />
                <span className="text-sm text-muted-foreground">Connected</span>
              </>
            )}
          </div>
          <BalanceToggle />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
