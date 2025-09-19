import { createRootRoute, Outlet } from "@tanstack/react-router";
import { AppSidebar } from "../components/AppSidebar";
import { SiteHeader } from "../components/SiteHeader";
import { PWAInstallPrompt, PWAUpdatePrompt } from "../components/PWAPrompts";
import { usePWA } from "../hooks/usePWA";
import {
  SidebarInset,
  SidebarProvider,
} from "../components/ui/sidebar";

function RootLayout() {
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
    <SidebarProvider
      style={
        {
          "--sidebar-width": "16rem",
          "--header-height": "4rem",
        } as React.CSSProperties
      }
    >
      <AppSidebar />
      <SidebarInset>
        <SiteHeader />
        <main className="flex-1 p-6 min-w-0">
          <Outlet />
        </main>
      </SidebarInset>

      {/* PWA Prompts */}
      <PWAInstallPrompt onInstall={handlePWAInstall} />
      <PWAUpdatePrompt
        updateAvailable={updateAvailable}
        onUpdate={handlePWAUpdate}
      />
    </SidebarProvider>
  );
}

export const Route = createRootRoute({
  component: RootLayout,
});
