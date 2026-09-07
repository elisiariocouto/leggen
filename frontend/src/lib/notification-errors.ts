import { getApiError } from "./api";

/**
 * Turn a failed test-notification request into a message that says what the
 * user should do next.
 *
 * The backend distinguishes the two failure modes by `code`:
 * `NOTIFICATION_NOT_ENABLED` (400) means nothing was sent because the service
 * is missing credentials or switched off — a settings fix — while
 * `UPSTREAM_ERROR` (502) means the provider itself refused or was unreachable,
 * which is worth retrying. Anything else falls back to the envelope's own
 * `detail`.
 */
export function getTestNotificationErrorMessage(
  error: unknown,
  serviceLabel: string,
): string {
  const apiError = getApiError(error);

  switch (apiError?.code) {
    case "NOTIFICATION_NOT_ENABLED":
      return `${serviceLabel} notifications are not configured or are disabled. Save a valid configuration first.`;
    case "UPSTREAM_ERROR":
      return `${serviceLabel} rejected the test notification. Check the credentials and try again.`;
    default:
      return (
        apiError?.detail ?? `Failed to send test ${serviceLabel} notification.`
      );
  }
}
