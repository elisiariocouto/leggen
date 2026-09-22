import type { ReactNode } from "react";
import { cn } from "../../lib/utils";
import { Skeleton } from "../ui/skeleton";

interface AnalyticsPanelProps {
  title: ReactNode;
  subtitle?: ReactNode;
  /** Controls beside the heading: toggles, tabs, a link out. */
  actions?: ReactNode;
  className?: string;
  isLoading?: boolean;
  /** When set, shown in place of the content. */
  empty?: ReactNode;
  /** Height of the loading and empty placeholders, sized to the content. */
  placeholderClassName?: string;
  children?: ReactNode;
}

/**
 * The heading, loading skeleton and empty state every analytics widget
 * shares. A widget returns one of these for each state, so the frame keeps
 * its place while data arrives and only the body changes.
 */
export default function AnalyticsPanel({
  title,
  subtitle,
  actions,
  className,
  isLoading = false,
  empty,
  placeholderClassName = "h-80",
  children,
}: AnalyticsPanelProps) {
  return (
    <div className={className}>
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-medium text-foreground">{title}</h3>
          {subtitle && (
            <p className="text-sm text-muted-foreground">{subtitle}</p>
          )}
        </div>
        {actions}
      </div>
      {isLoading ? (
        <Skeleton className={cn("w-full", placeholderClassName)} />
      ) : empty ? (
        <div
          className={cn(
            "flex flex-col items-center justify-center gap-1 text-center text-muted-foreground",
            placeholderClassName,
          )}
        >
          {empty}
        </div>
      ) : (
        children
      )}
    </div>
  );
}
