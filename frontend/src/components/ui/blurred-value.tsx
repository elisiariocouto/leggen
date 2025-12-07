import React from "react";
import { useBalanceVisibility } from "../../contexts/BalanceVisibilityContext";
import { cn } from "../../lib/utils";

interface BlurredValueProps {
  children: React.ReactNode;
  className?: string;
}

export function BlurredValue({ children, className }: BlurredValueProps) {
  const { isBalanceVisible } = useBalanceVisibility();

  return (
    <span
      className={cn(
        isBalanceVisible ? "" : "blur-md select-none",
        className,
      )}
    >
      {children}
    </span>
  );
}
