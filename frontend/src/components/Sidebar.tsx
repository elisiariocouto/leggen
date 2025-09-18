import { Link, useLocation } from "@tanstack/react-router";
import {
  List,
  BarChart3,
  Bell,
  TrendingUp,
  X,
  ChevronDown,
  ChevronUp,
  Settings,
  Building2,
} from "lucide-react";
import { Logo } from "./ui/logo";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../lib/api";
import { formatCurrency } from "../lib/utils";
import { cn } from "../lib/utils";
import { useState } from "react";
import type { Account } from "../types/api";


const navigation = [
  { name: "Overview", icon: List, to: "/" },
  { name: "Analytics", icon: BarChart3, to: "/analytics" },
  { name: "Notifications", icon: Bell, to: "/notifications" },
  { name: "Settings", icon: Settings, to: "/settings" },
];

interface SidebarProps {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

export default function Sidebar({ sidebarOpen, setSidebarOpen }: SidebarProps) {
  const location = useLocation();
  const [accountsExpanded, setAccountsExpanded] = useState(false);

  const { data: accounts } = useQuery<Account[]>({
    queryKey: ["accounts"],
    queryFn: apiClient.getAccounts,
  });

  const totalBalance =
    accounts?.reduce((sum, account) => {
      const primaryBalance = account.balances?.[0]?.amount || 0;
      return sum + primaryBalance;
    }, 0) || 0;

  return (
    <div
      className={cn(
        "fixed inset-y-0 left-0 z-50 w-64 bg-card shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0",
        sidebarOpen ? "translate-x-0" : "-translate-x-full",
      )}
    >
      <div className="flex items-center justify-between h-16 px-6 border-b border-border">
        <Link
          to="/"
          onClick={() => setSidebarOpen(false)}
          className="flex items-center space-x-2 hover:opacity-80 transition-opacity"
        >
          <Logo size={32} />
          <h1 className="text-xl font-bold text-card-foreground">Leggen</h1>
        </Link>
        <button
          onClick={() => setSidebarOpen(false)}
          className="lg:hidden p-1 rounded-md text-muted-foreground hover:text-foreground"
        >
          <X className="h-6 w-6" />
        </button>
      </div>

      <nav className="px-6 py-4">
        <div className="space-y-1">
          {navigation.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              onClick={() => setSidebarOpen(false)}
              className={cn(
                "flex items-center w-full px-3 py-2 text-sm font-medium rounded-md transition-colors",
                location.pathname === item.to
                  ? "bg-primary text-primary-foreground"
                  : "text-card-foreground hover:text-card-foreground hover:bg-accent",
              )}
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.name}
            </Link>
          ))}
        </div>
      </nav>

      {/* Collapsible Account Summary in Sidebar */}
      <div className="px-6 pt-4 pb-6 border-t border-border mt-auto">
        <div className="bg-muted rounded-lg">
          {/* Collapsible Header */}
          <button
            onClick={() => setAccountsExpanded(!accountsExpanded)}
            className="w-full p-4 flex items-center justify-between hover:bg-muted/80 transition-colors rounded-lg"
          >
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-muted-foreground">
                  Total Balance
                </span>
                <TrendingUp className="h-4 w-4 text-green-500" />
              </div>
              {accountsExpanded ? (
                <ChevronUp className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              )}
            </div>
          </button>

          <div className="px-4 pb-2">
            <p className="text-2xl font-bold text-foreground">
              {formatCurrency(totalBalance)}
            </p>
            <p className="text-sm text-muted-foreground">
              {accounts?.length || 0} accounts
            </p>
          </div>

          {/* Expanded Account Details */}
          {accountsExpanded && accounts && accounts.length > 0 && (
            <div className="border-t border-border/50 max-h-64 overflow-y-auto">
              {accounts.map((account) => {
                const primaryBalance = account.balances?.[0]?.amount || 0;
                const currency = account.balances?.[0]?.currency || account.currency || "EUR";

                return (
                  <div
                    key={account.id}
                    className="p-3 border-b border-border/30 last:border-b-0 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-start space-x-2">
                      <div className="flex-shrink-0 p-1 bg-background rounded">
                        <Building2 className="h-3 w-3 text-muted-foreground" />
                      </div>
                      <div className="space-y-1 min-w-0 flex-1">
                        <p className="text-sm font-medium text-foreground truncate">
                          {account.display_name || account.name || "Unnamed Account"}
                        </p>
                        <p className="text-sm font-semibold text-foreground">
                          {formatCurrency(primaryBalance, currency)}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
