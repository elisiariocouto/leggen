import { useLocation } from "@tanstack/react-router";
import { Menu, Activity, Wifi, WifiOff } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../lib/api";
import { ThemeToggle } from "./ui/theme-toggle";

const navigation = [
  { name: "Overview", to: "/" },
  { name: "Transactions", to: "/transactions" },
  { name: "Analytics", to: "/analytics" },
  { name: "Notifications", to: "/notifications" },
];

interface HeaderProps {
  setSidebarOpen: (open: boolean) => void;
}

export default function Header({ setSidebarOpen }: HeaderProps) {
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
    <header className="bg-card shadow-sm border-b border-border">
      <div className="flex items-center justify-between h-16 px-6">
        <div className="flex items-center">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-1 rounded-md text-muted-foreground hover:text-foreground"
          >
            <Menu className="h-6 w-6" />
          </button>
          <h2 className="text-lg font-semibold text-card-foreground lg:ml-0 ml-4">
            {currentPage}
          </h2>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1">
            {healthLoading ? (
              <>
                <Activity className="h-4 w-4 text-yellow-500 animate-pulse" />
                <span className="text-sm text-muted-foreground">
                  Checking...
                </span>
              </>
            ) : healthError || healthStatus?.status !== "healthy" ? (
              <>
                <WifiOff className="h-4 w-4 text-red-500" />
                <span className="text-sm text-red-500">Disconnected</span>
              </>
            ) : (
              <>
                <Wifi className="h-4 w-4 text-green-500" />
                <span className="text-sm text-muted-foreground">Connected</span>
              </>
            )}
          </div>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
