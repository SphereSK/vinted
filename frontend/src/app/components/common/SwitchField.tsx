"use client";

import { Switch } from "@/components/ui/switch";

interface SwitchFieldProps {
  label: string;
  description?: string;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
}

export function SwitchField({
  label,
  description,
  checked,
  onCheckedChange,
}: SwitchFieldProps) {
  return (
    <label className="flex flex-1 items-start gap-3 rounded-lg border p-3">
      <Switch checked={checked} onCheckedChange={onCheckedChange} />
      <span>
        <span className="block font-medium">{label}</span>
        {description && (
          <span className="text-sm text-muted-foreground">{description}</span>
        )}
      </span>
    </label>
  );
}
