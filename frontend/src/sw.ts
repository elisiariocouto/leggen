/// <reference lib="webworker" />

import { cleanupOutdatedCaches, precacheAndRoute } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { NetworkFirst } from 'workbox-strategies';

declare let self: ServiceWorkerGlobalScope;

// Clean up old caches
cleanupOutdatedCaches();

// Precache assets
precacheAndRoute(self.__WB_MANIFEST);

// Runtime caching for API calls
registerRoute(
  /^https:\/\/.*\/api\//,
  new NetworkFirst({
    cacheName: 'api-cache',
    networkTimeoutSeconds: 10,
    plugins: [
      {
        cacheKeyWillBeUsed: async ({ request }) => {
          // Use a stable cache key for API requests
          return `${request.url}?${Date.now()}`;
        },
      },
    ],
  })
);

// Push event handler
self.addEventListener('push', (event) => {
  console.log('Push received:', event);

  let data = {
    title: 'Leggen',
    body: 'You have a new notification',
    icon: '/pwa-192x192.png',
    badge: '/pwa-64x64.png',
    data: { url: '/' },
  };

  if (event.data) {
    try {
      const pushData = event.data.json();
      data = { ...data, ...pushData };
    } catch (e) {
      console.error('Failed to parse push data:', e);
    }
  }

  const options: NotificationOptions = {
    body: data.body,
    icon: data.icon,
    badge: data.badge,
    data: data.data,
    requireInteraction: true,
    // Note: 'actions' is not part of the standard NotificationOptions interface
    // but is supported by some browsers. We'll handle actions in the click handler.
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  console.log('Notification click received:', event);

  event.notification.close();

  const url = event.notification.data?.url || '/';

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients: readonly Client[]) => {
      // Check if there's already a window/tab open with the target URL
      for (const client of windowClients) {
        if (client.url === url && 'focus' in client) {
          return (client as WindowClient).focus();
        }
      }

      // If no suitable window is found, open a new one
      if (self.clients.openWindow) {
        return self.clients.openWindow(url);
      }
    })
  );
});

// Handle service worker messages (for subscription management)
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
