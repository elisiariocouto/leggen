import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { tanstackRouter } from "@tanstack/router-vite-plugin";
import { VitePWA } from "vite-plugin-pwa";

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    tanstackRouter(),
    react(),
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
            url: "/transactions",
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
        manualChunks: {
          "vendor-router": [
            "@tanstack/react-router",
            "@tanstack/react-query",
          ],
          "vendor-ui": [
            "@radix-ui/react-alert-dialog",
            "@radix-ui/react-checkbox",
            "@radix-ui/react-dialog",
            "@radix-ui/react-dropdown-menu",
            "@radix-ui/react-label",
            "@radix-ui/react-popover",
            "@radix-ui/react-select",
            "@radix-ui/react-switch",
            "@radix-ui/react-tooltip",
          ],
          "vendor-charts": ["recharts"],
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
          "vendor-table": [
            "@tanstack/react-table",
            "@dnd-kit/core",
            "@dnd-kit/sortable",
            "@dnd-kit/modifiers",
            "@dnd-kit/utilities",
          ],
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
