"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

// =============== StatCard ===============
interface StatCardProps {
  title: string;
  value: number | string | null | undefined;
  caption?: string;
  loading?: boolean;
}

export function StatCard({ title, value, caption, loading }: StatCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-1">
        <span className="text-3xl font-semibold tracking-tight">
          {loading ? (
            <Loader2 className="size-6 animate-spin text-muted-foreground" />
          ) : value !== null && value !== undefined ? (
            value
          ) : (
            "—"
          )}
        </span>
        {caption && <span className="text-xs text-muted-foreground">{caption}</span>}
      </CardContent>
    </Card>
  );
}

// =============== TrendPill ===============
interface TrendPillProps {
  label: string;
  value: number;
  tone: "up" | "down" | "neutral";
}

export function TrendPill({ label, value, tone }: TrendPillProps) {
  const toneClasses = {
    up: "bg-emerald-500/10 text-emerald-500 border-emerald-500/30",
    down: "bg-red-500/10 text-red-500 border-red-500/30",
    neutral: "bg-muted text-muted-foreground border-transparent",
  } as const;

  return (
    <div
      className={cn(
        "flex flex-col gap-0.5 rounded-lg border px-4 py-3",
        toneClasses[tone],
      )}
    >
      <span className="text-xs uppercase tracking-wide">{label}</span>
      <span className="text-xl font-semibold">{value}</span>
    </div>
  );
}
