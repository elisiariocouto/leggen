import { Monitor, Moon, Sun } from "lucide-react";
import { Button } from "./button";
import { useTheme } from "../../contexts/ThemeContext";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  const cycleTheme = () => {
    if (theme === "light") {
      setTheme("dark");
    } else if (theme === "dark") {
      setTheme("system");
    } else {
      setTheme("light");
    }
  };

  const getIcon = () => {
    switch (theme) {
      case "light":
        return <Sun className="h-4 w-4" />;
      case "dark":
        return <Moon className="h-4 w-4" />;
      case "system":
        return <Monitor className="h-4 w-4" />;
    }
  };

  const getLabel = () => {
    switch (theme) {
      case "light":
        return "Switch to dark mode";
      case "dark":
        return "Switch to system mode";
      case "system":
        return "Switch to light mode";
    }
  };

  return (
    <Button
      variant="outline"
      size="icon"
      onClick={cycleTheme}
      className="h-8 w-8"
      title={getLabel()}
    >
      {getIcon()}
      <span className="sr-only">{getLabel()}</span>
    </Button>
  );
}
