"use client";

import { useState, useEffect } from "react";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";

interface CronSchedulerProps {
  value: string;
  onChange: (cronExpression: string) => void;
}

type ScheduleType = "preset" | "builder" | "custom";

const PRESET_OPTIONS = [
  { value: "*/15 * * * *", label: "Every 15 minutes" },
  { value: "*/30 * * * *", label: "Every 30 minutes" },
  { value: "0 * * * *", label: "Every hour (at :00)" },
  { value: "0 */2 * * *", label: "Every 2 hours (at :00)" },
  { value: "0 */3 * * *", label: "Every 3 hours (at :00)" },
  { value: "0 */6 * * *", label: "Every 6 hours (at :00)" },
  { value: "0 */12 * * *", label: "Every 12 hours (at :00)" },
  { value: "0 0 * * *", label: "Daily at midnight" },
  { value: "0 9 * * *", label: "Daily at 9:00 AM" },
  { value: "0 18 * * *", label: "Daily at 6:00 PM" },
  { value: "0 9 * * 1-5", label: "Weekdays at 9:00 AM" },
  { value: "0 18 * * 1-5", label: "Weekdays at 6:00 PM" },
];

const INTERVAL_OPTIONS = [
  { value: "hour", label: "Hour(s)" },
  { value: "day", label: "Day(s)" },
];

const WEEKDAY_OPTIONS = [
  { value: "1", label: "Mon" },
  { value: "2", label: "Tue" },
  { value: "3", label: "Wed" },
  { value: "4", label: "Thu" },
  { value: "5", label: "Fri" },
  { value: "6", label: "Sat" },
  { value: "0", label: "Sun" },
];

export function CronScheduler({ value, onChange }: CronSchedulerProps) {
  const [scheduleType, setScheduleType] = useState<ScheduleType>("preset");
  const [selectedPreset, setSelectedPreset] = useState(value || PRESET_OPTIONS[0].value);

  // Builder state
  const [intervalType, setIntervalType] = useState<"hour" | "day">("hour");
  const [intervalValue, setIntervalValue] = useState("1");
  const [minute, setMinute] = useState("0");
  const [hour, setHour] = useState("0");
  const [selectedWeekdays, setSelectedWeekdays] = useState<string[]>([]);

  // Custom manual input
  const [customCron, setCustomCron] = useState(value || "0 * * * *");

  // Parse existing cron to determine which tab to show
  useEffect(() => {
    if (!value) return;

    const matchesPreset = PRESET_OPTIONS.some(p => p.value === value);
    if (matchesPreset) {
      setScheduleType("preset");
      setSelectedPreset(value);
    } else {
      // Try to parse it for builder or show as custom
      const parts = value.split(" ");
      if (parts.length === 5) {
        const [min, hr, dom, mon, dow] = parts;

        // Check if it's a simple interval pattern
        if (hr.startsWith("*/") && min === "0" && dom === "*" && mon === "*" && dow === "*") {
          setScheduleType("builder");
          setIntervalType("hour");
          setIntervalValue(hr.replace("*/", ""));
          setMinute("0");
        } else if (hr !== "*" && dom === "*" && mon === "*" && dow === "*") {
          setScheduleType("builder");
          setIntervalType("day");
          setHour(hr);
          setMinute(min);
        } else {
          setScheduleType("custom");
          setCustomCron(value);
        }
      } else {
        setScheduleType("custom");
        setCustomCron(value);
      }
    }
  }, [value]);

  const buildCronExpression = (): string => {
    if (intervalType === "hour") {
      return `${minute} */${intervalValue} * * *`;
    } else if (intervalType === "day") {
      if (selectedWeekdays.length > 0) {
        // Weekly schedule
        return `${minute} ${hour} * * ${selectedWeekdays.sort((a, b) => Number(a) - Number(b)).join(",")}`;
      } else {
        // Daily schedule
        return `${minute} ${hour} * * *`;
      }
    }
    return "0 * * * *";
  };

  const handlePresetChange = (preset: string) => {
    setSelectedPreset(preset);
    onChange(preset);
  };

  const handleBuilderChange = () => {
    const cron = buildCronExpression();
    onChange(cron);
  };

  useEffect(() => {
    if (scheduleType === "builder") {
      handleBuilderChange();
    }
  }, [intervalType, intervalValue, minute, hour, selectedWeekdays, scheduleType]);

  const toggleWeekday = (day: string) => {
    setSelectedWeekdays(prev =>
      prev.includes(day)
        ? prev.filter(d => d !== day)
        : [...prev, day]
    );
  };

  const getReadableSchedule = (cron: string): string => {
    const preset = PRESET_OPTIONS.find(p => p.value === cron);
    if (preset) return preset.label;

    const parts = cron.split(" ");
    if (parts.length !== 5) return cron;

    const [min, hr, dom, mon, dow] = parts;

    if (hr.startsWith("*/")) {
      const hours = hr.replace("*/", "");
      return `Every ${hours} hour${hours !== "1" ? "s" : ""} at :${min.padStart(2, "0")}`;
    }

    if (dow !== "*" && hr !== "*" && min !== "*") {
      const days = dow.split(",").map(d => {
        const day = WEEKDAY_OPTIONS.find(opt => opt.value === d);
        return day?.label || d;
      }).join(", ");
      return `${days} at ${hr.padStart(2, "0")}:${min.padStart(2, "0")}`;
    }

    if (hr !== "*" && dom === "*" && mon === "*" && dow === "*") {
      return `Daily at ${hr.padStart(2, "0")}:${min.padStart(2, "0")}`;
    }

    return cron;
  };

  const currentCronExpression = scheduleType === "preset"
    ? selectedPreset
    : scheduleType === "builder"
      ? buildCronExpression()
      : customCron;

  return (
    <div className="grid gap-4">
      <Tabs value={scheduleType} onValueChange={(v) => setScheduleType(v as ScheduleType)}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="preset">Presets</TabsTrigger>
          <TabsTrigger value="builder">Builder</TabsTrigger>
          <TabsTrigger value="custom">Custom</TabsTrigger>
        </TabsList>

        {/* Preset Tab */}
        <TabsContent value="preset" className="space-y-4">
          <div className="grid gap-2">
            <Label>Select schedule preset</Label>
            <Select value={selectedPreset} onValueChange={handlePresetChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PRESET_OPTIONS.map((preset) => (
                  <SelectItem key={preset.value} value={preset.value}>
                    {preset.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </TabsContent>

        {/* Builder Tab */}
        <TabsContent value="builder" className="space-y-4">
          <div className="grid gap-4">
            {/* Interval Type */}
            <div className="grid gap-2">
              <Label>Run every</Label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  min="1"
                  max="23"
                  value={intervalValue}
                  onChange={(e) => setIntervalValue(e.target.value)}
                  className="w-20"
                />
                <Select value={intervalType} onValueChange={(v) => setIntervalType(v as "hour" | "day")}>
                  <SelectTrigger className="w-[120px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {INTERVAL_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Minute selector */}
            <div className="grid gap-2">
              <Label>At minute</Label>
              <Select value={minute} onValueChange={setMinute}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="max-h-60">
                  {Array.from({ length: 60 }, (_, i) => (
                    <SelectItem key={i} value={String(i)}>
                      :{String(i).padStart(2, "0")}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Hour selector (only for daily) */}
            {intervalType === "day" && (
              <div className="grid gap-2">
                <Label>At hour</Label>
                <Select value={hour} onValueChange={setHour}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="max-h-60">
                    {Array.from({ length: 24 }, (_, i) => (
                      <SelectItem key={i} value={String(i)}>
                        {String(i).padStart(2, "0")}:00
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Weekday selector (only for daily) */}
            {intervalType === "day" && (
              <div className="grid gap-2">
                <Label>Days of week (optional - leave empty for daily)</Label>
                <div className="flex flex-wrap gap-2">
                  {WEEKDAY_OPTIONS.map((day) => (
                    <Badge
                      key={day.value}
                      variant={selectedWeekdays.includes(day.value) ? "default" : "outline"}
                      className="cursor-pointer"
                      onClick={() => toggleWeekday(day.value)}
                    >
                      {day.label}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </TabsContent>

        {/* Custom Tab */}
        <TabsContent value="custom" className="space-y-4">
          <div className="grid gap-2">
            <Label>Cron expression</Label>
            <Input
              value={customCron}
              onChange={(e) => {
                setCustomCron(e.target.value);
                onChange(e.target.value);
              }}
              placeholder="0 * * * *"
              className="font-mono"
            />
            <p className="text-xs text-muted-foreground">
              Format: minute hour day month weekday
            </p>
          </div>
        </TabsContent>
      </Tabs>

      {/* Preview */}
      <div className="rounded-md border bg-muted/50 p-3">
        <div className="flex items-center justify-between gap-2">
          <div className="text-sm">
            <span className="font-medium">Schedule: </span>
            <span className="text-muted-foreground">{getReadableSchedule(currentCronExpression)}</span>
          </div>
          <code className="rounded bg-background px-2 py-1 text-xs font-mono">
            {currentCronExpression}
          </code>
        </div>
      </div>
    </div>
  );
}
