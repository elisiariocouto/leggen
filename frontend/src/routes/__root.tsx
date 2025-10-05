import { createRootRoute, Outlet } from "@tanstack/react-router";
import { AppSidebar } from "../components/AppSidebar";
import { SiteHeader } from "../components/SiteHeader";
import { SidebarInset, SidebarProvider } from "../components/ui/sidebar";
import { Toaster } from "../components/ui/sonner";

function RootLayout() {
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

      {/* Toast Notifications */}
      <Toaster />
    </SidebarProvider>
  );
}

export const Route = createRootRoute({
  component: RootLayout,
});
