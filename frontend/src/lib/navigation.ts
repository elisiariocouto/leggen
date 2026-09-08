import {
  ArrowLeftRight,
  BarChart3,
  Building2,
  RefreshCw,
  Settings,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

/**
 * The app's top-level destinations, in sidebar order.
 *
 * Shared by the sidebar, the header (which uses `name` to title the current
 * page) and the command palette, so a new route is added in one place rather
 * than in three lists that drift apart.
 */
export interface NavigationItem {
  name: string;
  to: string;
  icon: LucideIcon;
}

export const navigation: NavigationItem[] = [
  { name: "Transactions", icon: ArrowLeftRight, to: "/" },
  { name: "Analytics", icon: BarChart3, to: "/analytics" },
  { name: "Accounts", icon: Building2, to: "/accounts" },
  { name: "Sync", icon: RefreshCw, to: "/sync" },
  { name: "Settings", icon: Settings, to: "/settings" },
];
