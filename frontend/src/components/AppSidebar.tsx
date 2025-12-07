import React from "react";
import { Link, useLocation } from "@tanstack/react-router";
import {
  List,
  BarChart3,
  Activity,
  Settings,
  Building2,
  TrendingUp,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Logo } from "./ui/logo";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../lib/api";
import { formatCurrency } from "../lib/utils";
import { useState } from "react";
import type { Account } from "../types/api";
import { BlurredValue } from "./ui/blurred-value";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  useSidebar,
} from "./ui/sidebar";

const navigation = [
  { name: "Overview", icon: List, to: "/" },
  { name: "Analytics", icon: BarChart3, to: "/analytics" },
  { name: "System", icon: Activity, to: "/system" },
  { name: "Settings", icon: Settings, to: "/settings" },
];

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const location = useLocation();
  const [accountsExpanded, setAccountsExpanded] = useState(false);
  const { isMobile, setOpenMobile } = useSidebar();

  const { data: accounts } = useQuery<Account[]>({
    queryKey: ["accounts"],
    queryFn: apiClient.getAccounts,
  });

  const totalBalance =
    accounts?.reduce((sum, account) => {
      const primaryBalance = account.balances?.[0]?.amount || 0;
      return sum + primaryBalance;
    }, 0) || 0;

  // Handler to close mobile sidebar when navigation item is clicked
  const handleNavigationClick = () => {
    if (isMobile) {
      setOpenMobile(false);
    }
  };

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              className="data-[slot=sidebar-menu-button]:!p-1.5"
            >
              <Link
                to="/"
                className="flex items-center space-x-2"
                onClick={handleNavigationClick}
              >
                <Logo size={24} />
                <span className="text-base font-semibold">Leggen</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {navigation.map((item) => (
                <SidebarMenuItem key={item.to}>
                  <SidebarMenuButton
                    asChild
                    tooltip={item.name}
                    isActive={location.pathname === item.to}
                  >
                    <Link to={item.to} onClick={handleNavigationClick}>
                      <item.icon className="h-5 w-5" />
                      <span>{item.name}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        {/* Account Summary Section */}
        <SidebarGroup>
          <SidebarGroupLabel>Account Summary</SidebarGroupLabel>
          <div className="bg-muted rounded-lg p-1">
            {/* Collapsible Header */}
            <button
              onClick={() => setAccountsExpanded(!accountsExpanded)}
              className="w-full p-3 flex items-center justify-between hover:bg-muted/80 transition-colors rounded-lg"
            >
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
            </button>

            <div className="px-3 pb-2">
              <p className="text-xl font-bold text-foreground">
                <BlurredValue>{formatCurrency(totalBalance)}</BlurredValue>
              </p>
              <p className="text-sm text-muted-foreground">
                {accounts?.length || 0} accounts
              </p>
            </div>

            {/* Expanded Account Details */}
            {accountsExpanded && accounts && accounts.length > 0 && (
              <div className="border-t border-border/50 max-h-48 overflow-y-auto">
                {accounts.map((account) => {
                  const primaryBalance = account.balances?.[0]?.amount || 0;
                  const currency =
                    account.balances?.[0]?.currency ||
                    account.currency ||
                    "EUR";

                  return (
                    <div
                      key={account.id}
                      className="p-2 border-b border-border/30 last:border-b-0 hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-start space-x-2">
                        <div className="flex-shrink-0 p-1 bg-background rounded">
                          <Building2 className="h-3 w-3 text-muted-foreground" />
                        </div>
                        <div className="space-y-1 min-w-0 flex-1">
                          <p className="text-xs font-medium text-foreground truncate">
                            {account.display_name ||
                              account.name ||
                              "Unnamed Account"}
                          </p>
                          <p className="text-xs font-semibold text-foreground">
                            <BlurredValue>
                              {formatCurrency(primaryBalance, currency)}
                            </BlurredValue>
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </SidebarGroup>
      </SidebarFooter>
    </Sidebar>
  );
}
