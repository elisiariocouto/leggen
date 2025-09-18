import { useEffect, useState } from "react";

interface PWAUpdate {
  updateAvailable: boolean;
  updateSW: () => Promise<void>;
}

export function usePWA(): PWAUpdate {
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [updateSW, setUpdateSW] = useState<() => Promise<void>>(() => async () => {});

  useEffect(() => {
    // Check if SW registration is available
    if ("serviceWorker" in navigator) {
      // Import the registerSW function
      import("virtual:pwa-register").then(({ registerSW }) => {
        const updateSWFunction = registerSW({
          onNeedRefresh() {
            setUpdateAvailable(true);
            setUpdateSW(() => updateSWFunction);
          },
          onOfflineReady() {
            console.log("App ready to work offline");
          },
        });
      }).catch(() => {
        // PWA not available in development mode or when disabled
        console.log("PWA registration not available");
      });
    }
  }, []);

  return {
    updateAvailable,
    updateSW,
  };
}
