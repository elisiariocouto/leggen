import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { tanstackRouter } from "@tanstack/router-vite-plugin";
import { VitePWA } from "vite-plugin-pwa";

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    tanstackRouter(),
    react(),
    tailwindcss(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: [
        "robots.txt"
      ],
      manifest: {
        name: "Leggen",
        short_name: "Leggen",
        description: "Personal finance management application",
        theme_color: "#0b74de",
        background_color: "#ffffff",
        display: "standalone",
        orientation: "portrait",
        scope: "/",
        start_url: "/",
        categories: ["finance", "productivity"],
        shortcuts: [
          {
            name: "Transactions",
            short_name: "Transactions",
            description: "View and manage transactions",
            url: "/",
            icons: [{ src: "/pwa-192x192.png", sizes: "192x192" }],
          },
          {
            name: "Analytics",
            short_name: "Analytics",
            description: "View financial analytics",
            url: "/analytics",
            icons: [{ src: "/pwa-192x192.png", sizes: "192x192" }],
          },
        ],
        icons: [
          {
            src: "pwa-64x64.png",
            sizes: "64x64",
            type: "image/png",
          },
          {
            src: "pwa-192x192.png",
            sizes: "192x192",
            type: "image/png",
          },
          {
            src: "pwa-512x512.png",
            sizes: "512x512",
            type: "image/png",
          },
          {
            src: "maskable-icon-512x512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "maskable",
          },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,ico,png,svg}"],
        runtimeCaching: [
          {
            urlPattern: /^https?:\/\/.*\/api\/v1\/health/,
            handler: "NetworkOnly",
          },
          {
            urlPattern: /^https:\/\/.*\/api\//,
            handler: "NetworkFirst",
            options: {
              cacheName: "api-cache",
              networkTimeoutSeconds: 10,
              cacheableResponse: {
                statuses: [0, 200],
              },
            },
          },
        ],
      },
      devOptions: {
        enabled: true,
      },
    }),
  ],
  build: {
    rollupOptions: {
      output: {
        // Vite 8 (rolldown) takes a function here; the object form is gone.
        // recharts is deliberately unlisted — it is reachable only through
        // the lazily-imported analytics route, so leaving it unassigned
        // keeps it in that route's chunk instead of the initial graph.
        manualChunks: (id: string) => {
          if (!id.includes("node_modules")) return;
          const vendors: Record<string, string[]> = {
            "vendor-router": [
              "@tanstack/react-router",
              "@tanstack/react-query",
            ],
            "vendor-ui": ["@radix-ui/"],
            "vendor-utils": [
              "date-fns",
              "lucide-react",
              "axios",
              "cmdk",
              "sonner",
              "vaul",
              "clsx",
              "tailwind-merge",
              "class-variance-authority",
            ],
          };
          for (const [chunk, packages] of Object.entries(vendors)) {
            if (packages.some((pkg) => id.includes(`node_modules/${pkg}`))) {
              return chunk;
            }
          }
        },
      },
    },
  },
  resolve: {
    alias: {
      "@": "/src",
    },
  },
});
