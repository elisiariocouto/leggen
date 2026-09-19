import {
  addDays,
  addMonths,
  differenceInCalendarDays,
  differenceInCalendarMonths,
  endOfMonth,
  format,
  isFirstDayOfMonth,
  isLastDayOfMonth,
  isToday,
  parseISO,
  startOfMonth,
} from "date-fns";

/**
 * Helpers for the "yyyy-MM-dd" date ranges the filters keep in the URL.
 *
 * A range is either two bounds or none; the pickers never produce a
 * one-sided range, though a hand-edited URL can.
 */

export interface DateRangeValue {
  startDate: string;
  endDate: string;
}

const ISO = "yyyy-MM-dd";

/**
 * Whether the range is a run of whole calendar months. The end may also be
 * today: "this month so far" is what a month-to-date preset and a partial
 * matrix column both produce, and it should step and label like a month.
 */
export function isMonthAligned(startDate: string, endDate: string): boolean {
  if (!startDate || !endDate) return false;
  const start = parseISO(startDate);
  const end = parseISO(endDate);
  if (end < start) return false;
  return isFirstDayOfMonth(start) && (isLastDayOfMonth(end) || isToday(end));
}

/**
 * The range's name, for the picker button and the filter chip: a whole
 * month reads as "March 2026", a whole year as "2025", a run of whole
 * months as "Jan – Mar 2026", and anything else as its two dates.
 */
export function describeRange(startDate: string, endDate: string): string {
  if (!startDate || !endDate) return "";
  const start = parseISO(startDate);
  const end = parseISO(endDate);

  if (startDate === endDate) return format(start, "MMM d, yyyy");

  if (isFirstDayOfMonth(start) && isLastDayOfMonth(end)) {
    const months = differenceInCalendarMonths(end, start) + 1;
    if (months === 1) return format(start, "MMMM yyyy");
    if (months === 12 && start.getMonth() === 0) return format(start, "yyyy");
    return start.getFullYear() === end.getFullYear()
      ? `${format(start, "MMM")} – ${format(end, "MMM yyyy")}`
      : `${format(start, "MMM yyyy")} – ${format(end, "MMM yyyy")}`;
  }

  return start.getFullYear() === end.getFullYear()
    ? `${format(start, "MMM d")} – ${format(end, "MMM d, yyyy")}`
    : `${format(start, "MMM d, yyyy")} – ${format(end, "MMM d, yyyy")}`;
}

/**
 * The same range one period earlier or later. Whole months step by months,
 * so the month after February is all of March rather than 28 days of it;
 * anything else slides by its own length in days.
 */
export function shiftRange(
  startDate: string,
  endDate: string,
  direction: -1 | 1,
): DateRangeValue {
  const start = parseISO(startDate);
  const end = parseISO(endDate);

  if (isMonthAligned(startDate, endDate)) {
    const months = differenceInCalendarMonths(end, start) + 1;
    const nextStart = startOfMonth(addMonths(start, direction * months));
    const nextEnd = endOfMonth(addMonths(nextStart, months - 1));
    return { startDate: format(nextStart, ISO), endDate: format(nextEnd, ISO) };
  }

  const days = differenceInCalendarDays(end, start) + 1;
  return {
    startDate: format(addDays(start, direction * days), ISO),
    endDate: format(addDays(end, direction * days), ISO),
  };
}
