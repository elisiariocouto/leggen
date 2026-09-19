import { useState } from "react";
import { format, parseISO } from "date-fns";
import {
  Calendar as CalendarIcon,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import type { DateRange } from "react-day-picker";

import { cn } from "@/lib/utils";
import { describeRange, shiftRange } from "@/lib/dateRanges";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export interface DatePreset {
  label: string;
  getValue: () => { startDate: string; endDate: string };
}

export interface DateRangePickerProps {
  startDate: string;
  endDate: string;
  onDateRangeChange: (startDate: string, endDate: string) => void;
  /** Presets shown as a dropdown below the calendar. If omitted, no presets are shown. */
  presets?: DatePreset[];
  className?: string;
}

/**
 * A date range: the calendar for any span, presets for the usual ones, and
 * arrows that step the current span back and forth — a whole month to the
 * neighbouring month, anything else by its own length. A reader who has
 * landed on one month of the category matrix walks to the next one from
 * here rather than through the calendar.
 */
export function DateRangePicker({
  startDate,
  endDate,
  onDateRangeChange,
  presets,
  className,
}: DateRangePickerProps) {
  const [open, setOpen] = useState(false);

  // Convert string dates to Date objects for the calendar.
  // parseISO/format work in local time — new Date("YYYY-MM-DD") and
  // toISOString() go through UTC and shift the date in non-UTC zones.
  const dateRange: DateRange | undefined =
    startDate && endDate
      ? {
          from: parseISO(startDate),
          to: parseISO(endDate),
        }
      : undefined;

  const handleDateRangeSelect = (range: DateRange | undefined) => {
    if (range?.from && range?.to) {
      onDateRangeChange(
        format(range.from, "yyyy-MM-dd"),
        format(range.to, "yyyy-MM-dd"),
      );
    } else if (range?.from && !range?.to) {
      onDateRangeChange(
        format(range.from, "yyyy-MM-dd"),
        format(range.from, "yyyy-MM-dd"),
      );
    }
  };

  const handlePresetChange = (value: string) => {
    const preset = presets?.find((p) => p.label === value);
    if (preset) {
      const { startDate: presetStart, endDate: presetEnd } = preset.getValue();
      onDateRangeChange(presetStart, presetEnd);
      setOpen(false);
    }
  };

  const matchingPresetLabel = presets?.find((preset) => {
    const { startDate: presetStart, endDate: presetEnd } = preset.getValue();
    return presetStart === startDate && presetEnd === endDate;
  })?.label;

  const formatDateRange = () => {
    // Before the empty-bounds check: a preset may legitimately have no
    // bounds ("All time"), and its label should win over the placeholder.
    if (matchingPresetLabel) {
      return matchingPresetLabel;
    }

    if (!startDate || !endDate) {
      return "Select date range";
    }

    return describeRange(startDate, endDate);
  };

  // Stepping needs a bounded span to step. Forward stops once the span
  // would start after today: nothing lives there yet.
  const canStep = Boolean(startDate && endDate);
  const today = format(new Date(), "yyyy-MM-dd");
  const canStepForward = canStep && shiftRange(startDate, endDate, 1).startDate <= today;
  const step = (direction: -1 | 1) => {
    const next = shiftRange(startDate, endDate, direction);
    onDateRangeChange(next.startDate, next.endDate);
  };

  return (
    <div className={cn("flex items-stretch", className)}>
      {canStep && (
        <Button
          variant="outline"
          size="icon"
          className="rounded-r-none border-r-0"
          aria-label="Previous period"
          onClick={() => step(-1)}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
      )}
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger
          render={
            <Button
              variant="outline"
              className={cn(
                "min-w-0 flex-1 justify-between text-left font-normal",
                canStep && "rounded-none",
                !dateRange && "text-muted-foreground",
              )}
            >
              <div className="flex min-w-0 items-center">
                <CalendarIcon className="mr-2 h-4 w-4 shrink-0" />
                <span className="truncate">{formatDateRange()}</span>
              </div>
              <ChevronDown className="h-4 w-4 shrink-0 opacity-50" />
            </Button>
          }
        />
        <PopoverContent className="w-auto p-0" align="start">
          <Card className="w-auto pt-4">
            <CardContent className="px-4">
              <Calendar
                mode="range"
                defaultMonth={dateRange?.from}
                selected={dateRange}
                onSelect={handleDateRangeSelect}
                className="bg-transparent p-0"
              />
            </CardContent>
            {presets && presets.length > 0 && (
              <CardFooter className="border-t px-4 pt-4! pb-4!">
                <Select
                  value={matchingPresetLabel ?? ""}
                  onValueChange={handlePresetChange}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Quick select..." />
                  </SelectTrigger>
                  <SelectContent>
                    {presets.map((preset) => (
                      <SelectItem key={preset.label} value={preset.label}>
                        {preset.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </CardFooter>
            )}
          </Card>
        </PopoverContent>
      </Popover>
      {canStep && (
        <Button
          variant="outline"
          size="icon"
          className="rounded-l-none border-l-0"
          aria-label="Next period"
          disabled={!canStepForward}
          onClick={() => step(1)}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}
