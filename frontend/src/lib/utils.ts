import { clsx, type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatCurrency(amount: number, currency: string = 'EUR'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
  }).format(amount);
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
