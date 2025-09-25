import { useEffect, useState } from "react";

interface PWAUpdate {
  updateAvailable: boolean;
  updateSW: () => Promise<void>;
  forceReload: () => Promise<void>;
}

export function usePWA(): PWAUpdate {
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [updateSW, setUpdateSW] = useState<() => Promise<void>>(
    () => async () => {},
  );

  const forceReload = async (): Promise<void> => {
    try {
      // Clear all caches
      if ("caches" in window) {
        const cacheNames = await caches.keys();
        await Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName)),
        );
        console.log("All caches cleared");
      }

      // Unregister service worker
      if ("serviceWorker" in navigator) {
        const registrations = await navigator.serviceWorker.getRegistrations();
        await Promise.all(
          registrations.map((registration) => registration.unregister()),
        );
        console.log("All service workers unregistered");
      }

      // Force reload
      window.location.reload();
    } catch (error) {
      console.error("Error during force reload:", error);
      // Fallback: just reload the page
      window.location.reload();
    }
  };

  useEffect(() => {
    // Check if SW registration is available
    if ("serviceWorker" in navigator) {
      // Import the registerSW function
      import("virtual:pwa-register")
        .then(({ registerSW }) => {
          const updateSWFunction = registerSW({
            onNeedRefresh() {
              setUpdateAvailable(true);
              setUpdateSW(() => updateSWFunction);
            },
            onOfflineReady() {
              console.log("App ready to work offline");
            },
          });
        })
        .catch(() => {
          // PWA not available in development mode or when disabled
          console.log("PWA registration not available");
        });
    }
  }, []);

  return {
    updateAvailable,
    updateSW,
    forceReload,
  };
}
