"use client";

import { Search, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Card, CardContent } from "@/components/ui/card";
import { FilterSection } from "./FilterSection";
import { FilterChips } from "./FilterChips";
import type {
  FilterRequest,
  CategoryResponse,
  PlatformResponse,
  SourceResponse,
  ConditionResponse,
} from "@/lib/types";

interface FilterPanelProps {
  filters: FilterRequest;
  onFilterChange: (key: keyof FilterRequest, value: string | number | string[] | undefined) => void;
  onFiltersChange: (updates: Partial<FilterRequest>) => void;
  onClearFilters: () => void;
  categories: CategoryResponse[];
  platforms: PlatformResponse[];
  sources: SourceResponse[];
  conditions: ConditionResponse[];
  totalResults?: number;
  isLoading?: boolean;
  className?: string;
}

export function FilterPanel({
  filters,
  onFilterChange,
  onFiltersChange,
  onClearFilters,
  categories,
  platforms,
  sources,
  conditions,
  totalResults = 0,
  isLoading = false,
  className = "",
}: FilterPanelProps) {
  const handleRemoveFilter = (key: keyof FilterRequest, value?: string) => {
    if (value && Array.isArray(filters[key])) {
      // Remove specific value from array
      const currentValues = filters[key] as string[];
      onFilterChange(
        key,
        currentValues.filter((v) => v !== value)
      );
    } else {
      // Clear entire filter
      onFilterChange(key, Array.isArray(filters[key]) ? [] : undefined);
    }
  };

  const handlePriceChange = (values: number[]) => {
    onFiltersChange({
      price_min: values[0],
      price_max: values[1],
    });
  };

  const maxPrice = 1000; // Default max price for slider

  return (
    <Card className={className}>
      <CardContent className="p-6">
        <div className="space-y-6">
          {/* Header with results count */}
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Filters</h3>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Loading...</span>
                </>
              ) : (
                <span>
                  {totalResults} {totalResults === 1 ? "result" : "results"}
                </span>
              )}
            </div>
          </div>

          {/* Active filter chips */}
          <FilterChips
            filters={filters}
            onRemoveFilter={handleRemoveFilter}
            onClearAll={onClearFilters}
          />

          {/* Search input */}
          <div className="space-y-2">
            <Label htmlFor="title-search">Search in title</Label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="title-search"
                placeholder="Search by title..."
                value={filters.title || ""}
                onChange={(e) => onFilterChange("title", e.target.value)}
                className="pl-9"
              />
            </div>
          </div>

          {/* Price range slider */}
          <div className="space-y-4">
            <Label>Price range (€)</Label>
            <div className="px-2">
              <Slider
                value={[filters.price_min || 0, filters.price_max || maxPrice]}
                onValueChange={handlePriceChange}
                max={maxPrice}
                min={0}
                step={1}
                className="w-full"
              />
            </div>
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <Label htmlFor="price-min" className="text-xs text-muted-foreground">
                  Min
                </Label>
                <Input
                  id="price-min"
                  type="number"
                  placeholder="0"
                  value={filters.price_min || ""}
                  onChange={(e) =>
                    onFilterChange("price_min", e.target.value ? Number(e.target.value) : undefined)
                  }
                  className="h-8"
                />
              </div>
              <span className="pt-5 text-muted-foreground">—</span>
              <div className="flex-1">
                <Label htmlFor="price-max" className="text-xs text-muted-foreground">
                  Max
                </Label>
                <Input
                  id="price-max"
                  type="number"
                  placeholder={String(maxPrice)}
                  value={filters.price_max || ""}
                  onChange={(e) =>
                    onFilterChange("price_max", e.target.value ? Number(e.target.value) : undefined)
                  }
                  className="h-8"
                />
              </div>
            </div>
          </div>

          {/* Multi-select filters */}
          <div className="grid gap-4 md:grid-cols-2">
            <FilterSection
              label="Condition"
              options={conditions}
              selectedValues={filters.conditions || []}
              onSelectionChange={(values) => onFilterChange("conditions", values)}
              placeholder="All conditions"
              searchPlaceholder="Search conditions..."
            />

            <FilterSection
              label="Platform"
              options={platforms}
              selectedValues={filters.platforms || []}
              onSelectionChange={(values) => onFilterChange("platforms", values)}
              placeholder="All platforms"
              searchPlaceholder="Search platforms..."
            />

            <FilterSection
              label="Source"
              options={sources}
              selectedValues={filters.sources || []}
              onSelectionChange={(values) => onFilterChange("sources", values)}
              placeholder="All sources"
              searchPlaceholder="Search sources..."
            />

            <FilterSection
              label="Category"
              options={categories}
              selectedValues={filters.categories || []}
              onSelectionChange={(values) => onFilterChange("categories", values)}
              placeholder="All categories"
              searchPlaceholder="Search categories..."
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
