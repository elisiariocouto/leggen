import React, { createContext, useContext, useEffect, useState } from "react";

type Theme = "light" | "dark" | "system";

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  actualTheme: "light" | "dark";
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    const stored = localStorage.getItem("theme") as Theme;
    return stored || "system";
  });

  const [actualTheme, setActualTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    const root = window.document.documentElement;

    const updateActualTheme = () => {
      let resolvedTheme: "light" | "dark";

      if (theme === "system") {
        resolvedTheme = window.matchMedia("(prefers-color-scheme: dark)")
          .matches
          ? "dark"
          : "light";
      } else {
        resolvedTheme = theme;
      }

      setActualTheme(resolvedTheme);

      // Remove previous theme classes
      root.classList.remove("light", "dark");

      // Add resolved theme class
      root.classList.add(resolvedTheme);
    };

    updateActualTheme();

    // Listen for system theme changes
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = () => {
      if (theme === "system") {
        updateActualTheme();
      }
    };

    mediaQuery.addEventListener("change", handleChange);

    // Store theme preference
    localStorage.setItem("theme", theme);

    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme, actualTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
