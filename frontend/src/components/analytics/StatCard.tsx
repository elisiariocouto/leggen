import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { BlurredValue } from "../ui/blurred-value";
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
  iconColor?: "green" | "blue" | "red" | "purple" | "orange" | "default";
  shouldBlur?: boolean;
}

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  className,
  iconColor = "default",
  shouldBlur = false,
}: StatCardProps) {
  return (
    <Card className={cn(className)}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <div className="flex items-baseline">
              <p className="text-2xl font-bold text-foreground">
                {shouldBlur ? <BlurredValue>{value}</BlurredValue> : value}
              </p>
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
            </div>
            {subtitle && (
              <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>
            )}
          </div>
          <div
            className={cn(
              "p-3 rounded-full",
              iconColor === "green" && "bg-green-100 dark:bg-green-900/20",
              iconColor === "blue" && "bg-blue-100 dark:bg-blue-900/20",
              iconColor === "red" && "bg-red-100 dark:bg-red-900/20",
              iconColor === "purple" && "bg-purple-100 dark:bg-purple-900/20",
              iconColor === "orange" && "bg-orange-100 dark:bg-orange-900/20",
              iconColor === "default" && "bg-muted",
            )}
          >
            <Icon
              className={cn(
                "h-6 w-6",
                iconColor === "green" && "text-green-600",
                iconColor === "blue" && "text-blue-600",
                iconColor === "red" && "text-red-600",
                iconColor === "purple" && "text-purple-600",
                iconColor === "orange" && "text-orange-600",
                iconColor === "default" && "text-muted-foreground",
              )}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
