import {
  createRootRoute,
  Link,
  Outlet,
  redirect,
  useLocation,
} from "@tanstack/react-router";
import { AppSidebar } from "../components/AppSidebar";
import { SiteHeader } from "../components/SiteHeader";
import ErrorBoundary from "../components/ErrorBoundary";
import { SidebarInset, SidebarProvider } from "../components/ui/sidebar";
import { Toaster } from "../components/ui/sonner";
import { CommandPalette } from "../components/CommandPalette";
import { useCommandPalette } from "../hooks/use-command-palette";
import { hasValidSession } from "../lib/authToken";

// Routes reachable without a session. Everything else redirects to /login.
const PUBLIC_ROUTES = new Set(["/login", "/bank-connected"]);

function RootLayout() {
  const location = useLocation();
  // Called before the login early-return because hooks cannot be
  // conditional; the palette itself is only rendered once past it.
  const { open: paletteOpen, setOpen: setPaletteOpen } = useCommandPalette();

  // The login screen is full-bleed: no sidebar, no header.
  if (location.pathname === "/login") {
    return (
      <>
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
        <Toaster />
      </>
    );
  }

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
        <SiteHeader onOpenCommandPalette={() => setPaletteOpen(true)} />
        <main className="flex-1 p-6 min-w-0">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </SidebarInset>

      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />

      {/* Toast Notifications */}
      <Toaster />
    </SidebarProvider>
  );
}

function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <h1 className="text-4xl font-bold text-foreground">404</h1>
      <p className="text-muted-foreground">
        The page you're looking for doesn't exist.
      </p>
      <Link to="/" className="text-primary underline underline-offset-4">
        Go to Transactions
      </Link>
    </div>
  );
}

export const Route = createRootRoute({
  // Runs before the component tree mounts, so an unauthenticated visitor
  // never renders a frame of the app. This replaces an effect that fired
  // after the first paint and needed a null-return guard to compensate.
  beforeLoad: ({ location }) => {
    if (PUBLIC_ROUTES.has(location.pathname)) return;
    if (!hasValidSession()) {
      throw redirect({
        to: "/login",
        // Come back here once signed in.
        search: { redirect: location.href },
      });
    }
  },
  component: RootLayout,
  notFoundComponent: NotFound,
});
