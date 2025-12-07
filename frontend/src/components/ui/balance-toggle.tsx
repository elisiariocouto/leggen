import { Eye, EyeOff } from "lucide-react";
import { Button } from "./button";
import { useBalanceVisibility } from "../../contexts/BalanceVisibilityContext";

export function BalanceToggle() {
  const { isBalanceVisible, toggleBalanceVisibility } = useBalanceVisibility();

  return (
    <Button
      variant="outline"
      size="icon"
      onClick={toggleBalanceVisibility}
      className="h-8 w-8"
      title={isBalanceVisible ? "Hide balances" : "Show balances"}
    >
      {isBalanceVisible ? (
        <Eye className="h-4 w-4" />
      ) : (
        <EyeOff className="h-4 w-4" />
      )}
      <span className="sr-only">
        {isBalanceVisible ? "Hide balances" : "Show balances"}
      </span>
    </Button>
  );
}
