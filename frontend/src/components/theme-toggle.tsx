"use client";

import { useEffect, useState } from "react";
import { MoonStar, Sun } from "lucide-react";
import { useTheme } from "next-themes";

import { Button } from "@/components/ui/button";

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <Button variant="outline" size="icon" aria-label="Loading theme">
        <Sun className="size-4" />
      </Button>
    );
  }

  const isDark = resolvedTheme === "dark";

  return (
    <Button
      type="button"
      variant="outline"
      size="icon"
      className="relative overflow-hidden"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      aria-label="Toggle theme"
    >
      <Sun className={`size-4 transition-all ${isDark ? "-rotate-90 scale-0" : "rotate-0 scale-100"}`} />
      <MoonStar className={`absolute size-4 transition-all ${isDark ? "rotate-0 scale-100" : "rotate-90 scale-0"}`} />
    </Button>
  );
}
