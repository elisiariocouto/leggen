import type { ReactNode } from "react";
import type { UseQueryResult } from "@tanstack/react-query";
import type { LucideIcon } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../ui/card";
import { Skeleton } from "../ui/skeleton";
import QueryErrorAlert from "../QueryErrorAlert";

interface SettingsCardProps<T> {
  icon: LucideIcon;
  title: string;
  description?: string;
  /** Beside the title, normally the drawer that edits this section. */
  action?: ReactNode;
  /** The query this card shows; it loads and fails on its own. */
  query: UseQueryResult<T>;
  children: (data: T) => ReactNode;
}

/**
 * One section of the settings page. Each card waits on its own query, so a
 * slow or failing endpoint blanks only its own section instead of the page.
 */
export default function SettingsCard<T>({
  icon: Icon,
  title,
  description,
  action,
  query,
  children,
}: SettingsCardProps<T>) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <Icon className="h-5 w-5 text-primary" />
            <span>{title}</span>
          </CardTitle>
          {query.isSuccess && action}
        </div>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      {query.isSuccess ? (
        children(query.data)
      ) : (
        <CardContent>
          {query.isError ? (
            <QueryErrorAlert
              title={`Failed to load ${title.toLowerCase()}`}
              onRetry={() => query.refetch()}
            />
          ) : (
            <Skeleton className="h-16 w-full" />
          )}
        </CardContent>
      )}
    </Card>
  );
}
