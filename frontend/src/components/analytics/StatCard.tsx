import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { cn } from "../../lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  className?: string;
}

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  className,
}: StatCardProps) {
  return (
    <Card className={cn(className)}>
      <CardContent className="p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <Icon className="h-8 w-8 text-primary" />
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-muted-foreground truncate">
                {title}
              </dt>
              <dd className="flex items-baseline">
                <div className="text-2xl font-semibold text-foreground">
                  {value}
                </div>
                {trend && (
                  <div
                    className={cn(
                      "ml-2 flex items-baseline text-sm font-semibold",
                      trend.isPositive
                        ? "text-green-600 dark:text-green-400"
                        : "text-red-600 dark:text-red-400",
                    )}
                  >
                    {trend.isPositive ? "+" : ""}
                    {trend.value}%
                  </div>
                )}
              </dd>
              {subtitle && (
                <dd className="text-sm text-muted-foreground mt-1">
                  {subtitle}
                </dd>
              )}
            </dl>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
