"use client";

import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { formatCurrency } from "@/lib/format";
import type { ListingResponse } from "@/lib/types";

interface PriceChangeBadgeProps {
  change: ListingResponse["price_change"];
  current: number | null | undefined;
  previous: number | null | undefined;
  currency?: string;
}

export function PriceChangeBadge({
  change,
  current,
  previous,
  currency,
}: PriceChangeBadgeProps) {
  if (!change || current == null || previous == null) {
    return <span className="text-muted-foreground text-xs">—</span>;
  }

  const toneClasses =
    change === "up"
      ? "bg-red-500/10 text-red-500"
      : change === "down"
      ? "bg-emerald-500/10 text-emerald-500"
      : "bg-muted text-muted-foreground";

  const Icon =
    change === "up" ? TrendingUp : change === "down" ? TrendingDown : Minus;

  const diff = current - previous;
  const absDiffLabel = formatCurrency(Math.abs(diff), currency);
  const diffLabel =
    diff > 0 ? `+${absDiffLabel}` : diff < 0 ? `-${absDiffLabel}` : absDiffLabel;

  const percent =
    previous !== 0 ? Math.abs((diff / previous) * 100).toFixed(1) + "%" : null;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium",
        toneClasses,
      )}
    >
      <Icon className="size-3" />
      {diffLabel}
      {percent && ` (${percent})`}
    </span>
  );
}
