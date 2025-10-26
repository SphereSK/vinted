"use client";

import { Badge } from "@/components/ui/badge";
import type { CategoryResponse } from "@/lib/types";

interface HelperListProps {
  items: CategoryResponse[];
}

export function HelperList({ items }: HelperListProps) {
  if (!items.length) return null;

  return (
    <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
      {items.slice(0, 6).map((item) => (
        <Badge key={item.id} variant="secondary">
          {item.id}: {item.name}
        </Badge>
      ))}
      {items.length > 6 && <span>…</span>}
    </div>
  );
}
