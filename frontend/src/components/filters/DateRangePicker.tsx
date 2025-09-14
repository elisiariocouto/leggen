import { useState } from "react";
import { format } from "date-fns";
import { Calendar as CalendarIcon, ChevronDown } from "lucide-react";
import type { DateRange } from "react-day-picker";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

export interface DateRangePickerProps {
  startDate: string;
  endDate: string;
  onDateRangeChange: (startDate: string, endDate: string) => void;
  className?: string;
}

interface DatePreset {
  label: string;
  getValue: () => { startDate: string; endDate: string };
}

const datePresets: DatePreset[] = [
  {
    label: "Last 7 days",
    getValue: () => {
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(endDate.getDate() - 7);
      return {
        startDate: startDate.toISOString().split("T")[0],
        endDate: endDate.toISOString().split("T")[0],
      };
    },
  },
  {
    label: "This week",
    getValue: () => {
      const now = new Date();
      const dayOfWeek = now.getDay();
      const startOfWeek = new Date(now);
      startOfWeek.setDate(now.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1)); // Monday as start

      const endOfWeek = new Date(startOfWeek);
      endOfWeek.setDate(startOfWeek.getDate() + 6);

      return {
        startDate: startOfWeek.toISOString().split("T")[0],
        endDate: endOfWeek.toISOString().split("T")[0],
      };
    },
  },
  {
    label: "Last 30 days",
    getValue: () => {
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(endDate.getDate() - 30);
      return {
        startDate: startDate.toISOString().split("T")[0],
        endDate: endDate.toISOString().split("T")[0],
      };
    },
  },
  {
    label: "This month",
    getValue: () => {
      const now = new Date();
      const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
      const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0);

      return {
        startDate: startOfMonth.toISOString().split("T")[0],
        endDate: endOfMonth.toISOString().split("T")[0],
      };
    },
  },
  {
    label: "This year",
    getValue: () => {
      const now = new Date();
      const startOfYear = new Date(now.getFullYear(), 0, 1);
      const endOfYear = new Date(now.getFullYear(), 11, 31);

      return {
        startDate: startOfYear.toISOString().split("T")[0],
        endDate: endOfYear.toISOString().split("T")[0],
      };
    },
  },
];

export function DateRangePicker({
  startDate,
  endDate,
  onDateRangeChange,
  className,
}: DateRangePickerProps) {
  const [open, setOpen] = useState(false);

  // Convert string dates to Date objects for the calendar
  const dateRange: DateRange | undefined =
    startDate && endDate
      ? {
          from: new Date(startDate),
          to: new Date(endDate),
        }
      : undefined;

  const handleDateRangeSelect = (range: DateRange | undefined) => {
    if (range?.from && range?.to) {
      onDateRangeChange(
        range.from.toISOString().split("T")[0],
        range.to.toISOString().split("T")[0]
      );
    } else if (range?.from && !range?.to) {
      onDateRangeChange(
        range.from.toISOString().split("T")[0],
        range.from.toISOString().split("T")[0]
      );
    }
  };

  const handlePresetClick = (preset: DatePreset) => {
    const { startDate: presetStart, endDate: presetEnd } = preset.getValue();
    onDateRangeChange(presetStart, presetEnd);
    setOpen(false);
  };

  const formatDateRange = () => {
    if (!startDate || !endDate) {
      return "Select date range";
    }

    const start = new Date(startDate);
    const end = new Date(endDate);

    // Check if it matches a preset
    const matchingPreset = datePresets.find((preset) => {
      const { startDate: presetStart, endDate: presetEnd } = preset.getValue();
      return presetStart === startDate && presetEnd === endDate;
    });

    if (matchingPreset) {
      return matchingPreset.label;
    }

    // Format custom range
    if (startDate === endDate) {
      return format(start, "MMM d, yyyy");
    }

    return `${format(start, "MMM d")} - ${format(end, "MMM d, yyyy")}`;
  };

  return (
    <div className={cn("grid gap-2", className)}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            className={cn(
              "justify-between text-left font-normal",
              !dateRange && "text-muted-foreground"
            )}
          >
            <div className="flex items-center">
              <CalendarIcon className="mr-2 h-4 w-4" />
              {formatDateRange()}
            </div>
            <ChevronDown className="h-4 w-4 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <div className="flex">
            {/* Presets */}
            <div className="border-r p-3 space-y-1">
              <div className="text-sm font-medium text-gray-700 mb-2">
                Quick select
              </div>
              {datePresets.map((preset) => (
                <Button
                  key={preset.label}
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-sm"
                  onClick={() => handlePresetClick(preset)}
                >
                  {preset.label}
                </Button>
              ))}
            </div>
            {/* Calendar */}
            <Calendar
              initialFocus
              mode="range"
              defaultMonth={dateRange?.from}
              selected={dateRange}
              onSelect={handleDateRangeSelect}
              numberOfMonths={2}
            />
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}
