import React, { createContext, useContext, useEffect, useState } from "react";

interface BalanceVisibilityContextType {
  isBalanceVisible: boolean;
  toggleBalanceVisibility: () => void;
}

const BalanceVisibilityContext = createContext<
  BalanceVisibilityContextType | undefined
>(undefined);

export function BalanceVisibilityProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isBalanceVisible, setIsBalanceVisible] = useState<boolean>(() => {
    const stored = localStorage.getItem("balanceVisible");
    // Default to true (visible) if not set
    return stored === null ? true : stored === "true";
  });

  useEffect(() => {
    localStorage.setItem("balanceVisible", String(isBalanceVisible));
  }, [isBalanceVisible]);

  const toggleBalanceVisibility = () => {
    setIsBalanceVisible((prev) => !prev);
  };

  return (
    <BalanceVisibilityContext.Provider
      value={{ isBalanceVisible, toggleBalanceVisibility }}
    >
      {children}
    </BalanceVisibilityContext.Provider>
  );
}

export function useBalanceVisibility() {
  const context = useContext(BalanceVisibilityContext);
  if (context === undefined) {
    throw new Error(
      "useBalanceVisibility must be used within a BalanceVisibilityProvider",
    );
  }
  return context;
}
