"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { X, ChevronDown } from "lucide-react";

interface MultiSelectOption {
  id: number;
  name: string;
  color?: string | null;
}

interface MultiSelectProps {
  label: string;
  options: MultiSelectOption[];
  selected: number[];
  onChange: (selected: number[]) => void;
  placeholder?: string;
}

export function MultiSelect({
  label,
  options,
  selected,
  onChange,
  placeholder = "Select items...",
}: MultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const toggleOption = (id: number) => {
    if (selected.includes(id)) {
      onChange(selected.filter((s) => s !== id));
    } else {
      onChange([...selected, id]);
    }
  };

  const removeOption = (id: number) => {
    onChange(selected.filter((s) => s !== id));
  };

  const selectedOptions = options.filter((opt) => selected.includes(opt.id));

  return (
    <div className="grid gap-2" ref={containerRef}>
      <Label>{label}</Label>
      <div className="relative">
        <Button
          type="button"
          variant="outline"
          className="w-full justify-between"
          onClick={() => setIsOpen(!isOpen)}
        >
          <span className="truncate">
            {selected.length > 0 ? `${selected.length} selected` : placeholder}
          </span>
          <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>

        {isOpen && (
          <div className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-md border bg-popover p-1 shadow-md">
            {options.length === 0 ? (
              <div className="px-2 py-1.5 text-sm text-muted-foreground">No options available</div>
            ) : (
              options.map((option) => (
                <div
                  key={option.id}
                  className="flex items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground cursor-pointer"
                  onClick={() => toggleOption(option.id)}
                >
                  <input
                    type="checkbox"
                    checked={selected.includes(option.id)}
                    onChange={() => {}} // Handled by onClick above
                    className="h-4 w-4 rounded border-gray-300"
                  />
                  <span className="flex-1">{option.name}</span>
                  <span className="text-xs text-muted-foreground">#{option.id}</span>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Selected items as badges */}
      {selectedOptions.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {selectedOptions.map((option) => (
            <Badge
              key={option.id}
              variant="secondary"
              className="gap-1"
              style={option.color ? { backgroundColor: option.color, color: "#fff" } : undefined}
            >
              {option.name}
              <button
                type="button"
                className="ml-1 rounded-full hover:bg-black/20"
                onClick={() => removeOption(option.id)}
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}
