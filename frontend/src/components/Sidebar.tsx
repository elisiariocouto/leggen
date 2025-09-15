import { Link, useLocation } from "@tanstack/react-router";
import {
  CreditCard,
  Home,
  List,
  BarChart3,
  Bell,
  TrendingUp,
  X,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../lib/api";
import { formatCurrency } from "../lib/utils";
import { cn } from "../lib/utils";
import type { Account } from "../types/api";

const navigation = [
  { name: "Overview", icon: Home, to: "/" },
  { name: "Transactions", icon: List, to: "/transactions" },
  { name: "Analytics", icon: BarChart3, to: "/analytics" },
  { name: "Notifications", icon: Bell, to: "/notifications" },
];

interface SidebarProps {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

export default function Sidebar({ sidebarOpen, setSidebarOpen }: SidebarProps) {
  const location = useLocation();

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
          <CreditCard className="h-8 w-8 text-primary" />
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

      {/* Account Summary in Sidebar */}
      <div className="px-6 py-4 border-t border-border mt-auto">
        <div className="bg-muted rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">
              Total Balance
            </span>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </div>
          <p className="text-2xl font-bold text-foreground mt-1">
            {formatCurrency(totalBalance)}
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            {accounts?.length || 0} accounts
          </p>
        </div>
      </div>
    </div>
  );
}
