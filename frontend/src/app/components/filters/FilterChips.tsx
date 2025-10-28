"use client";

import { X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { FilterRequest } from "@/lib/types";

interface FilterChipsProps {
  filters: FilterRequest;
  onRemoveFilter: (key: keyof FilterRequest, value?: string) => void;
  onClearAll: () => void;
  className?: string;
}

export function FilterChips({
  filters,
  onRemoveFilter,
  onClearAll,
  className = "",
}: FilterChipsProps) {
  const hasActiveFilters =
    filters.title ||
    filters.price_min !== undefined ||
    filters.price_max !== undefined ||
    (filters.conditions && filters.conditions.length > 0) ||
    (filters.platforms && filters.platforms.length > 0) ||
    (filters.sources && filters.sources.length > 0) ||
    (filters.categories && filters.categories.length > 0);

  if (!hasActiveFilters) {
    return null;
  }

  return (
    <div className={`flex flex-wrap items-center gap-2 ${className}`}>
      {filters.title && (
        <Badge variant="secondary" className="gap-1 pr-1">
          <span className="text-xs">Title: {filters.title}</span>
          <Button
            variant="ghost"
            size="icon-sm"
            className="h-4 w-4 p-0 hover:bg-transparent"
            onClick={() => onRemoveFilter("title")}
          >
            <X className="h-3 w-3" />
          </Button>
        </Badge>
      )}

      {(filters.price_min !== undefined || filters.price_max !== undefined) && (
        <Badge variant="secondary" className="gap-1 pr-1">
          <span className="text-xs">
            Price: {filters.price_min || 0}€ - {filters.price_max || "∞"}€
          </span>
          <Button
            variant="ghost"
            size="icon-sm"
            className="h-4 w-4 p-0 hover:bg-transparent"
            onClick={() => {
              onRemoveFilter("price_min");
              onRemoveFilter("price_max");
            }}
          >
            <X className="h-3 w-3" />
          </Button>
        </Badge>
      )}

      {filters.conditions?.map((condition) => (
        <Badge key={condition} variant="secondary" className="gap-1 pr-1">
          <span className="text-xs">Condition: {condition}</span>
          <Button
            variant="ghost"
            size="icon-sm"
            className="h-4 w-4 p-0 hover:bg-transparent"
            onClick={() => onRemoveFilter("conditions", condition)}
          >
            <X className="h-3 w-3" />
          </Button>
        </Badge>
      ))}

      {filters.platforms?.map((platform) => (
        <Badge key={platform} variant="secondary" className="gap-1 pr-1">
          <span className="text-xs">Platform: {platform}</span>
          <Button
            variant="ghost"
            size="icon-sm"
            className="h-4 w-4 p-0 hover:bg-transparent"
            onClick={() => onRemoveFilter("platforms", platform)}
          >
            <X className="h-3 w-3" />
          </Button>
        </Badge>
      ))}

      {filters.sources?.map((source) => (
        <Badge key={source} variant="secondary" className="gap-1 pr-1">
          <span className="text-xs">Source: {source}</span>
          <Button
            variant="ghost"
            size="icon-sm"
            className="h-4 w-4 p-0 hover:bg-transparent"
            onClick={() => onRemoveFilter("sources", source)}
          >
            <X className="h-3 w-3" />
          </Button>
        </Badge>
      ))}

      {filters.categories?.map((category) => (
        <Badge key={category} variant="secondary" className="gap-1 pr-1">
          <span className="text-xs">Category: {category}</span>
          <Button
            variant="ghost"
            size="icon-sm"
            className="h-4 w-4 p-0 hover:bg-transparent"
            onClick={() => onRemoveFilter("categories", category)}
          >
            <X className="h-3 w-3" />
          </Button>
        </Badge>
      ))}

      <Button
        variant="ghost"
        size="sm"
        onClick={onClearAll}
        className="h-7 text-xs text-muted-foreground hover:text-foreground"
      >
        Clear all
      </Button>
    </div>
  );
}
