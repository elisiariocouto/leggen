export type TimePeriod = {
  label: string;
  value: string;
  getDateRange: () => { startDate: string; endDate: string };
};

function toISODate(date: Date): string {
  return date.toISOString().split("T")[0];
}

export const TIME_PERIODS: TimePeriod[] = [
  {
    label: "Last 30 days",
    value: "30d",
    getDateRange: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - 30);
      return { startDate: toISODate(start), endDate: toISODate(end) };
    },
  },
  {
    label: "Last 6 months",
    value: "6m",
    getDateRange: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - 180);
      return { startDate: toISODate(start), endDate: toISODate(end) };
    },
  },
  {
    label: "Year to Date",
    value: "ytd",
    getDateRange: () => {
      const end = new Date();
      const start = new Date(end.getFullYear(), 0, 1);
      return { startDate: toISODate(start), endDate: toISODate(end) };
    },
  },
  {
    label: "Last 365 days",
    value: "365d",
    getDateRange: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - 365);
      return { startDate: toISODate(start), endDate: toISODate(end) };
    },
  },
];
