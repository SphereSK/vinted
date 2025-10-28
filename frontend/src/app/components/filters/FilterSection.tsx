"use client";

import { useState } from "react";
import { Check, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface FilterOption {
  id: number | string;
  name?: string;
  label?: string;
  color?: string | null;
}

interface FilterSectionProps {
  label: string;
  options: FilterOption[];
  selectedValues: string[];
  onSelectionChange: (values: string[]) => void;
  placeholder?: string;
  searchPlaceholder?: string;
  className?: string;
  labelField?: "name" | "label";
}

export function FilterSection({
  label,
  options,
  selectedValues,
  onSelectionChange,
  placeholder = "Select...",
  searchPlaceholder = "Search...",
  className = "",
  labelField = "name",
}: FilterSectionProps) {
  const [open, setOpen] = useState(false);

  const toggleOption = (value: string) => {
    const newValues = selectedValues.includes(value)
      ? selectedValues.filter((v) => v !== value)
      : [...selectedValues, value];
    onSelectionChange(newValues);
  };

  const clearSelection = () => {
    onSelectionChange([]);
  };

  const selectedCount = selectedValues.length;
  const getLabel = (option: FilterOption) => option[labelField] || option.name || option.label || "";

  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      {label && <label className="text-sm font-medium">{label}</label>}
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between"
          >
            <span className="flex items-center gap-2">
              {selectedCount > 0 ? (
                <>
                  <Badge variant="secondary" className="px-1.5 py-0">
                    {selectedCount}
                  </Badge>
                  <span className="truncate">
                    {selectedCount === 1
                      ? getLabel(options.find((opt) => selectedValues.includes(String(opt.id)))!)
                      : `${selectedCount} selected`}
                  </span>
                </>
              ) : (
                placeholder
              )}
            </span>
            <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[300px] p-0" align="start">
          <Command>
            <CommandInput placeholder={searchPlaceholder} />
            <CommandList>
              <CommandEmpty>No options found.</CommandEmpty>
              <CommandGroup>
                {options.map((option) => {
                  const isSelected = selectedValues.includes(String(option.id));
                  return (
                    <CommandItem
                      key={option.id}
                      value={String(option.id)}
                      onSelect={() => toggleOption(String(option.id))}
                    >
                      <div
                        className={cn(
                          "mr-2 flex h-4 w-4 items-center justify-center rounded-sm border border-primary",
                          isSelected
                            ? "bg-primary text-primary-foreground"
                            : "opacity-50 [&_svg]:invisible"
                        )}
                      >
                        <Check className="h-4 w-4" />
                      </div>
                      <span>{getLabel(option)}</span>
                      {option.color && (
                        <div
                          className="ml-auto h-3 w-3 rounded-full"
                          style={{ backgroundColor: option.color }}
                        />
                      )}
                    </CommandItem>
                  );
                })}
              </CommandGroup>
              {selectedCount > 0 && (
                <CommandGroup>
                  <CommandItem
                    onSelect={clearSelection}
                    className="justify-center text-center text-sm text-muted-foreground"
                  >
                    Clear selection
                  </CommandItem>
                </CommandGroup>
              )}
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
}
