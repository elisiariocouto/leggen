import { endOfMonth, format, startOfMonth, subMonths } from "date-fns";

export type TimePeriod = {
  label: string;
  value: string;
  getDateRange: () => { startDate: string; endDate: string };
};

// Format in local time — toISOString() converts to UTC first, which shifts
// the date by one day for anyone east of Greenwich
function toISODate(date: Date): string {
  return format(date, "yyyy-MM-dd");
}

function lastDays(days: number) {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - days);
  return { startDate: toISODate(start), endDate: toISODate(end) };
}

/**
 * Quick ranges shared by the home page and the transaction list. Calendar
 * periods come first: "last month" is the question a bank statement
 * answers, and stepping through months is how the matrix is read.
 */
export const TIME_PERIODS: TimePeriod[] = [
  {
    label: "This month",
    value: "month",
    getDateRange: () => {
      const today = new Date();
      return { startDate: toISODate(startOfMonth(today)), endDate: toISODate(today) };
    },
  },
  {
    label: "Last month",
    value: "prev-month",
    getDateRange: () => {
      const previous = subMonths(new Date(), 1);
      return {
        startDate: toISODate(startOfMonth(previous)),
        endDate: toISODate(endOfMonth(previous)),
      };
    },
  },
  { label: "Last 30 days", value: "30d", getDateRange: () => lastDays(30) },
  { label: "Last 6 months", value: "6m", getDateRange: () => lastDays(180) },
  {
    label: "Year to date",
    value: "ytd",
    getDateRange: () => {
      const end = new Date();
      const start = new Date(end.getFullYear(), 0, 1);
      return { startDate: toISODate(start), endDate: toISODate(end) };
    },
  },
  { label: "Last 365 days", value: "365d", getDateRange: () => lastDays(365) },
  {
    label: "Last year",
    value: "prev-year",
    getDateRange: () => {
      const year = new Date().getFullYear() - 1;
      return {
        startDate: toISODate(new Date(year, 0, 1)),
        endDate: toISODate(new Date(year, 11, 31)),
      };
    },
  },
];
