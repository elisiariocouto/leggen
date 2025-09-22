import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { TanStackRouterVite } from "@tanstack/router-vite-plugin";
import { VitePWA } from "vite-plugin-pwa";

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    TanStackRouterVite(),
    react(),
    VitePWA({
      strategies: "injectManifest",
      srcDir: "src",
      filename: "sw.ts",
      registerType: "autoUpdate",
      includeAssets: ["favicon.ico", "apple-touch-icon-180x180.png", "maskable-icon-512x512.png", "robots.txt"],
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
            icons: [{ src: "/pwa-192x192.png", sizes: "192x192" }]
          },
          {
            name: "Analytics",
            short_name: "Analytics",
            description: "View financial analytics",
            url: "/analytics",
            icons: [{ src: "/pwa-192x192.png", sizes: "192x192" }]
          }
        ],
         icons: [
           {
             src: "pwa-64x64.png",
             sizes: "64x64",
             type: "image/png",
             purpose: "any"
           },
           {
             src: "pwa-192x192.png",
             sizes: "192x192",
             type: "image/png",
             purpose: "any"
           },
           {
             src: "pwa-512x512.png",
             sizes: "512x512",
             type: "image/png",
             purpose: "any"
           },
           {
             src: "maskable-icon-512x512.png",
             sizes: "512x512",
             type: "image/png",
             purpose: "maskable"
           }
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
  resolve: {
    alias: {
      "@": "/src",
    },
  },
});
