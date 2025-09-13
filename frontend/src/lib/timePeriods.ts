export type TimePeriod = {
  label: string;
  days: number;
  value: string;
};

function getDaysFromYearStart(): number {
  const now = new Date();
  const yearStart = new Date(now.getFullYear(), 0, 1);
  const diffTime = now.getTime() - yearStart.getTime();
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

export const TIME_PERIODS: TimePeriod[] = [
  { label: "Last 30 days", days: 30, value: "30d" },
  { label: "Last 6 months", days: 180, value: "6m" },
  { label: "Year to Date", days: getDaysFromYearStart(), value: "ytd" },
  { label: "Last 365 days", days: 365, value: "365d" },
];