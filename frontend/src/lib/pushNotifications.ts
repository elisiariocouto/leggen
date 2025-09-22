import { apiClient } from './api';

export interface PushSubscriptionData {
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
}

export class PushNotificationManager {
  private registration: ServiceWorkerRegistration | null = null;
  private subscription: PushSubscription | null = null;

  async init(): Promise<void> {
    if (!('serviceWorker' in navigator)) {
      throw new Error('Service workers not supported');
    }

    if (!('PushManager' in navigator)) {
      throw new Error('Push notifications not supported');
    }

    // Check if we're running on HTTPS or localhost (localhost allowed for development)
    if (!window.location.protocol.startsWith('https') && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      throw new Error('Push notifications require HTTPS (or localhost for development)');
    }

    // Register service worker if not already registered
    if (!this.registration) {
      try {
        this.registration = await navigator.serviceWorker.register('/sw.js', {
          scope: '/',
        });
        console.log('Service worker registered:', this.registration);
      } catch (error) {
        console.error('Service worker registration failed:', error);
        throw new Error('Service worker registration failed');
      }
    }

    // Wait for the service worker to be ready
    try {
      await navigator.serviceWorker.ready;
      console.log('Service worker ready');
    } catch (error) {
      console.error('Service worker ready failed:', error);
      throw new Error('Service worker failed to become ready');
    }
  }

  async getSubscription(): Promise<PushSubscription | null> {
    if (!this.registration) {
      await this.init();
    }

    if (!this.registration) {
      return null;
    }

    this.subscription = await this.registration.pushManager.getSubscription();
    return this.subscription;
  }

  async subscribe(): Promise<PushSubscriptionData | null> {
    try {
      console.log('Starting push notification subscription...');

      if (!this.registration) {
        await this.init();
      }

      if (!this.registration) {
        throw new Error('Service worker not available');
      }

      console.log('Service worker ready, getting VAPID key...');

      // Get VAPID public key from server
      const vapidPublicKey = await apiClient.getPushPublicKey();
      console.log('VAPID key received:', vapidPublicKey ? 'yes' : 'no');

      if (!vapidPublicKey) {
        throw new Error('VAPID public key not configured on server');
      }

      // Extract base64 content from PEM format and convert to base64url
      const base64Key = extractBase64FromPEM(vapidPublicKey);
      const base64UrlKey = base64ToBase64Url(base64Key);
      console.log('Processed VAPID key for browser');

      // Convert VAPID key to Uint8Array
      const applicationServerKey = urlBase64ToUint8Array(base64UrlKey);

      console.log('Subscribing to push notifications...');

      // Subscribe to push notifications
      const subscription = await this.registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey,
      });

      console.log('Push subscription successful:', subscription.endpoint);

      this.subscription = subscription;

      // Convert subscription to our format
      const subscriptionData: PushSubscriptionData = {
        endpoint: subscription.endpoint,
        keys: {
          p256dh: arrayBufferToBase64(subscription.getKey('p256dh')!),
          auth: arrayBufferToBase64(subscription.getKey('auth')!),
        },
      };

      console.log('Sending subscription to server...');

      // Send subscription to server
      await apiClient.subscribePushNotifications(subscriptionData);

      console.log('Push notification subscription complete');

      return subscriptionData;
    } catch (error) {
      console.error('Failed to subscribe to push notifications:', error);
      throw error;
    }
  }

  async unsubscribe(): Promise<void> {
    try {
      const subscription = await this.getSubscription();

      if (subscription) {
        // Convert subscription to our format for server
        const subscriptionData: PushSubscriptionData = {
          endpoint: subscription.endpoint,
          keys: {
            p256dh: arrayBufferToBase64(subscription.getKey('p256dh')!),
            auth: arrayBufferToBase64(subscription.getKey('auth')!),
          },
        };

        // Unsubscribe from server
        await apiClient.unsubscribePushNotifications(subscriptionData);

        // Unsubscribe locally
        await subscription.unsubscribe();
      }

      this.subscription = null;
    } catch (error) {
      console.error('Failed to unsubscribe from push notifications:', error);
      throw error;
    }
  }

  async isSubscribed(): Promise<boolean> {
    const subscription = await this.getSubscription();
    return subscription !== null;
  }

  async requestPermission(): Promise<NotificationPermission> {
    if (!('Notification' in window)) {
      throw new Error('Notifications not supported');
    }

    const permission = await Notification.requestPermission();
    return permission;
  }

  getPermissionStatus(): NotificationPermission {
    if (!('Notification' in window)) {
      return 'denied';
    }

    return Notification.permission;
  }
}

// Utility functions
function extractBase64FromPEM(pemKey: string): string {
  // Remove PEM headers and footers, and join all lines
  const lines = pemKey.split('\n');
  const base64Lines = lines.slice(1, -1); // Remove first and last lines (headers)
  return base64Lines.join('').trim();
}

function base64ToBase64Url(base64: string): string {
  return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }

  return outputArray;
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}

// Export singleton instance
export const pushManager = new PushNotificationManager();
