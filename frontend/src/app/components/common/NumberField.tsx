"use client";

import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";

interface NumberFieldProps {
  label: string;
  value: number;
  min?: number;
  max?: number;
  step?: number;
  onChange: (value: number) => void;
}

export function NumberField({ label, value, min, max, step, onChange }: NumberFieldProps) {
  return (
    <div className="grid gap-2">
      <Label>{label}</Label>
      <Input
        type="number"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => {
          const next = Number(e.target.value);
          onChange(Number.isNaN(next) ? value : next);
        }}
      />
    </div>
  );
}
