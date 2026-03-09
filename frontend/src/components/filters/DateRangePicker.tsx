import { useState } from "react";
import { format } from "date-fns";
import { Calendar as CalendarIcon, ChevronDown } from "lucide-react";
import type { DateRange } from "react-day-picker";

import { cn } from "@/lib/utils";
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

export function DateRangePicker({
  startDate,
  endDate,
  onDateRangeChange,
  presets,
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
        range.to.toISOString().split("T")[0],
      );
    } else if (range?.from && !range?.to) {
      onDateRangeChange(
        range.from.toISOString().split("T")[0],
        range.from.toISOString().split("T")[0],
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
    if (!startDate || !endDate) {
      return "Select date range";
    }

    if (matchingPresetLabel) {
      return matchingPresetLabel;
    }

    const start = new Date(startDate);
    const end = new Date(endDate);

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
              !dateRange && "text-muted-foreground",
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
              <CardFooter className="border-t px-4 !pt-4 !pb-4">
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
    </div>
  );
}
