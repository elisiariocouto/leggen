import { createRootRoute, Outlet } from "@tanstack/react-router";
import { useState } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { PWAInstallPrompt, PWAUpdatePrompt } from "../components/PWAPrompts";
import { usePWA } from "../hooks/usePWA";

function RootLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { updateAvailable, updateSW } = usePWA();

  const handlePWAInstall = () => {
    console.log("PWA installed successfully");
  };

  const handlePWAUpdate = async () => {
    try {
      await updateSW();
      console.log("PWA updated successfully");
    } catch (error) {
      console.error("Error updating PWA:", error);
    }
  };

  return (
    <div className="flex h-screen bg-background">
      <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="flex flex-col flex-1 overflow-hidden">
        <Header setSidebarOpen={setSidebarOpen} />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>

      {/* PWA Prompts */}
      <PWAInstallPrompt onInstall={handlePWAInstall} />
      <PWAUpdatePrompt 
        updateAvailable={updateAvailable} 
        onUpdate={handlePWAUpdate} 
      />
    </div>
  );
}

export const Route = createRootRoute({
  component: RootLayout,
});
