import { clsx, type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatCurrency(amount: number, currency: string = 'EUR'): string {
  // Validate currency code - must be 3 letters and a valid ISO 4217 code
  const validCurrency = currency && /^[A-Z]{3}$/.test(currency) ? currency : 'EUR';

  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: validCurrency,
    }).format(amount);
  } catch (error) {
    // Fallback if currency is still invalid
    console.warn(`Invalid currency code: ${currency}, falling back to EUR`);
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount);
  }
}

export function formatDate(date: string): string {
  if (!date) return 'No date';

  const parsedDate = new Date(date);
  if (isNaN(parsedDate.getTime())) {
    console.warn('Invalid date string:', date);
    return 'Invalid date';
  }

  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(parsedDate);
}

export function formatDateTime(date: string): string {
  if (!date) return 'No date';

  const parsedDate = new Date(date);
  if (isNaN(parsedDate.getTime())) {
    console.warn('Invalid date string:', date);
    return 'Invalid date';
  }

  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(parsedDate);
}
