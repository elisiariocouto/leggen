import { RefreshCw } from "lucide-react";
import { cn } from "../lib/utils";

interface LoadingSpinnerProps {
  message?: string;
  className?: string;
}

export default function LoadingSpinner({
  message = "Loading...",
  className,
}: LoadingSpinnerProps) {
  return (
    <div className={cn("flex items-center justify-center p-8", className)}>
      <div className="text-center">
        <RefreshCw className="h-8 w-8 animate-spin text-primary mx-auto mb-2" />
        <p className="text-muted-foreground text-sm">{message}</p>
      </div>
    </div>
  );
}
