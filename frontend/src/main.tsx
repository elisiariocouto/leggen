import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createRouter, RouterProvider } from "@tanstack/react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "./contexts/ThemeContext";
import "./index.css";
import { routeTree } from "./routeTree.gen";
import { registerSW } from "virtual:pwa-register";

const router = createRouter({ routeTree });

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const intervalMS = 60 * 60 * 1000;

registerSW({
  onRegisteredSW(swUrl, r) {
    console.log("[PWA] Service worker registered successfully");

    if (r) {
      setInterval(async () => {
        console.log("[PWA] Checking for updates...");

        if (r.installing) {
          console.log("[PWA] Update already installing, skipping check");
          return;
        }

        if (!navigator) {
          console.log("[PWA] Navigator not available, skipping check");
          return;
        }

        if ("connection" in navigator && !navigator.onLine) {
          console.log("[PWA] Device is offline, skipping check");
          return;
        }

        try {
          const resp = await fetch(swUrl, {
            cache: "no-store",
            headers: {
              cache: "no-store",
              "cache-control": "no-cache",
            },
          });

          if (resp?.status === 200) {
            console.log("[PWA] Update check successful, triggering update");
            await r.update();
          } else {
            console.log(`[PWA] Update check returned status: ${resp?.status}`);
          }
        } catch (error) {
          console.error("[PWA] Error checking for updates:", error);
        }
      }, intervalMS);
    }
  },
  onOfflineReady() {
    console.log("[PWA] App ready to work offline");
  },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <RouterProvider router={router} />
      </ThemeProvider>
    </QueryClientProvider>
  </StrictMode>,
);
