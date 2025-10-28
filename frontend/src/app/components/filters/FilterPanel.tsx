"use client";

import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
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
  isSold?: boolean;
  onSoldChange?: (sold: boolean | undefined) => void;
  currency?: string;
  availableCurrencies?: string[];
  onCurrencyChange?: (currency: string | undefined) => void;
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
  isSold,
  onSoldChange,
  currency,
  availableCurrencies = [],
  onCurrencyChange,
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

  // Show all options from database (not filtered by current page)
  // This allows users to see and select all available filter values
  const availableConditions = conditions;
  const availablePlatforms = platforms;
  const availableSources = sources;
  const availableCategories = categories;

  return (
    <Card className={className}>
      <CardContent className="p-4">
        <div className="space-y-4">
          {/* Active filter chips */}
          <FilterChips
            filters={filters}
            onRemoveFilter={handleRemoveFilter}
            onClearAll={onClearFilters}
          />

          {/* All filters in one row */}
          <div className="flex flex-wrap items-end gap-2">
            {/* Search input */}
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search by title..."
                  value={filters.title || ""}
                  onChange={(e) => onFilterChange("title", e.target.value)}
                  className="pl-9 h-9"
                />
              </div>
            </div>

            {/* Price inputs */}
            <Input
              type="number"
              placeholder="Min price..."
              value={filters.price_min ?? ""}
              onChange={(e) =>
                onFilterChange("price_min", e.target.value ? Number(e.target.value) : undefined)
              }
              className="w-[110px] h-9"
            />
            <Input
              type="number"
              placeholder="Max price..."
              value={filters.price_max ?? ""}
              onChange={(e) =>
                onFilterChange("price_max", e.target.value ? Number(e.target.value) : undefined)
              }
              className="w-[110px] h-9"
            />

            {/* Multi-select filters */}
            <div className="w-[160px]">
              <FilterSection
                label=""
                options={availableConditions}
                selectedValues={filters.conditions || []}
                onSelectionChange={(values) => onFilterChange("conditions", values)}
                placeholder="Condition"
                searchPlaceholder="Search conditions..."
                labelField="label"
              />
            </div>

            <div className="w-[160px]">
              <FilterSection
                label=""
                options={availablePlatforms}
                selectedValues={filters.platforms || []}
                onSelectionChange={(values) => onFilterChange("platforms", values)}
                placeholder="Platform"
                searchPlaceholder="Search platforms..."
                labelField="name"
              />
            </div>

            <div className="w-[160px]">
              <FilterSection
                label=""
                options={availableSources}
                selectedValues={filters.sources || []}
                onSelectionChange={(values) => onFilterChange("sources", values)}
                placeholder="Source"
                searchPlaceholder="Search sources..."
                labelField="label"
              />
            </div>

            <div className="w-[160px]">
              <FilterSection
                label=""
                options={availableCategories}
                selectedValues={filters.categories || []}
                onSelectionChange={(values) => onFilterChange("categories", values)}
                placeholder="Category"
                searchPlaceholder="Search categories..."
                labelField="name"
              />
            </div>

            {/* Sold/Unsold Select */}
            {onSoldChange && (
              <Select
                value={isSold === undefined ? "ALL" : isSold ? "true" : "false"}
                onValueChange={(value) =>
                  onSoldChange(value === "ALL" ? undefined : value === "true")
                }
              >
                <SelectTrigger className="w-[130px] h-9">
                  <SelectValue placeholder="Sold Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Items</SelectItem>
                  <SelectItem value="false">Available</SelectItem>
                  <SelectItem value="true">Sold</SelectItem>
                </SelectContent>
              </Select>
            )}

            {/* Currency Select */}
            {onCurrencyChange && availableCurrencies.length > 0 && (
              <Select
                value={currency ?? "ALL"}
                onValueChange={(value) => onCurrencyChange(value === "ALL" ? undefined : value)}
              >
                <SelectTrigger className="w-[100px] h-9">
                  <SelectValue placeholder="Currency" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All</SelectItem>
                  {availableCurrencies.map((cur) => (
                    <SelectItem key={cur} value={cur}>
                      {cur}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}

            {/* Results count */}
            <div className="text-sm text-muted-foreground whitespace-nowrap ml-auto">
              {isLoading ? "Loading..." : `${totalResults} ${totalResults === 1 ? "result" : "results"}`}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
