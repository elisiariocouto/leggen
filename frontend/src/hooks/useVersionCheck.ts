import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../lib/api";

const VERSION_STORAGE_KEY = "leggen_app_version";

export function useVersionCheck(forceReload: () => Promise<void>) {
  const {
    data: healthStatus,
    isSuccess: healthSuccess,
  } = useQuery({
    queryKey: ["health"],
    queryFn: apiClient.getHealth,
    refetchInterval: 30000,
    retry: false,
    staleTime: 0, // Always consider data stale to ensure fresh version checks
  });

  useEffect(() => {
    if (healthSuccess && healthStatus?.version) {
      const currentVersion = healthStatus.version;
      const storedVersion = localStorage.getItem(VERSION_STORAGE_KEY);
      
      if (storedVersion && storedVersion !== currentVersion) {
        console.log(`Version mismatch detected: stored=${storedVersion}, current=${currentVersion}`);
        console.log("Clearing cache and reloading...");
        
        // Update stored version first
        localStorage.setItem(VERSION_STORAGE_KEY, currentVersion);
        
        // Force reload to clear cache
        forceReload();
      } else if (!storedVersion) {
        // First time loading, store the version
        localStorage.setItem(VERSION_STORAGE_KEY, currentVersion);
        console.log(`Version stored: ${currentVersion}`);
      }
    }
  }, [healthSuccess, healthStatus?.version, forceReload]);
}