"use client";

import { Badge } from "@/components/ui/badge";
import type { RuntimeStatusResponse } from "@/lib/types";
import { formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  status: RuntimeStatusResponse | null | undefined;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  if (!status) {
    return (
      <Badge variant="outline" className="text-muted-foreground">
        Idle
      </Badge>
    );
  }

  const tone =
    status.status === "success"
      ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/30"
      : status.status === "failed"
        ? "bg-red-500/10 text-red-500 border-red-500/30"
        : "bg-blue-500/10 text-blue-500 border-blue-500/30";

  return (
    <div className="flex flex-col gap-1">
      <Badge className={cn(tone)}>
        {status.status} · {status.items ?? 0} items
      </Badge>
      {status.message && (
        <span className="text-xs text-muted-foreground">{status.message}</span>
      )}
      <span className="text-xs text-muted-foreground">
        Updated {formatDate(status.updated_at)}
      </span>
    </div>
  );
}
