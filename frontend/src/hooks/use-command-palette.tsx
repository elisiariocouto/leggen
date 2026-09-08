import { useEffect, useState } from "react";

/**
 * Open state for the command palette, bound to Cmd/Ctrl+K.
 *
 * The listener sits on `window` so the shortcut works from anywhere,
 * including while a filter input has focus — Cmd+K is not a browser or
 * text-input default worth preserving. Mirrors the sidebar's Cmd+B binding
 * in `components/ui/sidebar.tsx`.
 */
export function useCommandPalette() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "k" && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        setOpen((previous) => !previous);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return { open, setOpen };
}
