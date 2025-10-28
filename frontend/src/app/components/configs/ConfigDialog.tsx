"use client";

import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { X, Loader2, Copy } from "lucide-react";
import { toast } from "sonner";

import type {
  ScrapeConfigResponse,
  ScrapeConfigWritePayload,
  CategoryResponse,
  CronCommandResponse,
} from "@/lib/types";
import { buildCronCommand } from "@/lib/endpoints";
import { useState, useEffect } from "react";
import { NumberField } from "../common/NumberField";
import { SwitchField } from "../common/SwitchField";
import { HelperList } from "../common/HelperList";
import { MultiSelect } from "../common/MultiSelect";
import { CronScheduler } from "../common/CronScheduler";

const ORDER_OPTIONS = [
  { value: "newest_first", label: "Newest first" },
  { value: "price_low_to_high", label: "Price low → high" },
  { value: "price_high_to_low", label: "Price high → low" },
];

const DETAIL_STRATEGY_OPTIONS = [
  { value: "browser" as const, label: "Browser (Chromium)" },
  { value: "http" as const, label: "HTTP requests" },
];

interface ConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  config: ScrapeConfigResponse | null;
  categories: CategoryResponse[];
  platforms: CategoryResponse[];
  onSave?: (payload: ScrapeConfigWritePayload) => Promise<void> | void;
}

export function ConfigDialog({
  open,
  onOpenChange,
  config,
  categories,
  platforms,
  onSave,
}: ConfigDialogProps) {
  // Helper to convert array to comma-separated string
  const arrayToString = (arr: (string | number)[] | null | undefined): string => {
    if (!arr || !Array.isArray(arr)) return "";
    return arr.join(",");
  };

  // Helper to convert number array to number array (for categories/platforms)
  const toNumberArray = (arr: number[] | null | undefined): number[] => {
    if (!arr || !Array.isArray(arr)) return [];
    return arr;
  };

  // Local editable state based on incoming config
  const [form, setForm] = useState(() =>
    config
      ? {
          ...config,
          categories: toNumberArray(config.categories),
          platform_ids: toNumberArray(config.platform_ids),
          extra_filters: arrayToString(config.extra_filters),
          locales: arrayToString(config.locales),
          extra_args: arrayToString(config.extra_args),
          base_url: config.base_url || "",
          order: config.order || "",
          cron_schedule: config.cron_schedule || "",
          healthcheck_ping_url: config.healthcheck_ping_url || "",
        }
      : {
          name: "",
          search_text: "",
          categories: [] as number[],
          platform_ids: [] as number[],
          order: "",
          extra_filters: "",
          locales: "",
          extra_args: "",
          max_pages: 5,
          per_page: 24,
          delay: 1,
          fetch_details: false,
          details_for_new_only: false,
          use_proxy: true,
          error_wait_minutes: 30,
          max_retries: 3,
          base_url: "",
          details_strategy: "browser" as const,
          details_concurrency: 2,
          cron_schedule: "",
          is_active: true,
          healthcheck_ping_url: "",
        },
  );

  useEffect(() => {
    if (config) {
      setForm({
        ...config,
        categories: toNumberArray(config.categories),
        platform_ids: toNumberArray(config.platform_ids),
        extra_filters: arrayToString(config.extra_filters),
        locales: arrayToString(config.locales),
        extra_args: arrayToString(config.extra_args),
        base_url: config.base_url || "",
        order: config.order || "",
        cron_schedule: config.cron_schedule || "",
        healthcheck_ping_url: config.healthcheck_ping_url || "",
      });
    } else {
      setForm({
        name: "",
        search_text: "",
        categories: [] as number[],
        platform_ids: [] as number[],
        order: "",
        extra_filters: "",
        locales: "",
        extra_args: "",
        max_pages: 5,
        per_page: 24,
        delay: 1,
        fetch_details: false,
        details_for_new_only: false,
        use_proxy: true,
        error_wait_minutes: 30,
        max_retries: 3,
        base_url: "",
        details_strategy: "browser" as const,
        details_concurrency: 2,
        cron_schedule: "",
        is_active: true,
        healthcheck_ping_url: "",
      });
    }
  }, [config]);

  const [isSaving, setIsSaving] = useState(false);
  const [preview, setPreview] = useState<CronCommandResponse | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);

  async function handlePreview() {
    setPreviewLoading(true);
    setPreviewError(null);
    try {
      const res = await buildCronCommand({
        schedule: form.cron_schedule,
        search_text: form.search_text,
      });
      setPreview(res);
    } catch (err) {
      setPreviewError(err instanceof Error ? err.message : "Failed to preview command");
      toast.error("Failed to preview cron command");
    } finally {
      setPreviewLoading(false);
    }
  }

  async function handleCopyPreview() {
    if (!preview?.command) return;
    try {
      await navigator.clipboard.writeText(preview.command);
      toast.success("Cron command copied");
    } catch {
      toast.error("Unable to copy to clipboard");
    }
  }

  // Helper to convert comma-separated string to array
  const stringToArray = (str: string): string[] | undefined => {
    const trimmed = str.trim();
    if (!trimmed) return undefined;
    return trimmed.split(",").map((s) => s.trim()).filter(Boolean);
  };

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (isSaving) return;
    setIsSaving(true);
    try {
      const payload: ScrapeConfigWritePayload = {
        name: form.name.trim(),
        search_text: form.search_text.trim(),
        categories: (form.categories as number[]).length > 0 ? (form.categories as number[]) : undefined,
        platform_ids: (form.platform_ids as number[]).length > 0 ? (form.platform_ids as number[]) : undefined,
        order: form.order || undefined,
        extra_filters: stringToArray(form.extra_filters as string),
        locales: stringToArray(form.locales as string),
        extra_args: stringToArray(form.extra_args as string),
        max_pages: form.max_pages,
        per_page: form.per_page,
        delay: form.delay,
        fetch_details: form.fetch_details,
        details_for_new_only: form.details_for_new_only,
        use_proxy: form.use_proxy,
        error_wait_minutes: form.error_wait_minutes || undefined,
        max_retries: form.max_retries || undefined,
        base_url: form.base_url || undefined,
        details_strategy: form.details_strategy,
        details_concurrency: form.details_concurrency,
        cron_schedule: form.cron_schedule || undefined,
        is_active: form.is_active,
        healthcheck_ping_url: form.healthcheck_ping_url || undefined,
      };
      if (onSave) await onSave(payload);
      toast.success("Configuration saved");
      onOpenChange(false);
    } catch (err) {
      toast.error("Failed to save configuration", {
        description: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="relative max-h-[85vh] max-w-5xl overflow-y-auto">
        <DialogClose asChild>
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="absolute right-3 top-3"
            aria-label="Close configuration dialog"
          >
            <X className="size-4" />
          </Button>
        </DialogClose>

        <form onSubmit={handleSubmit} className="grid gap-6">
          <DialogHeader>
            <DialogTitle>{config ? "Edit configuration" : "New configuration"}</DialogTitle>
            <DialogDescription>
              Configure search filters, scraping behavior, and scheduling for this job.
            </DialogDescription>
          </DialogHeader>

          {/* ── Basic fields ─────────────────────────────── */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="grid gap-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="search_text">Search text</Label>
              <Input
                id="search_text"
                value={form.search_text}
                onChange={(e) => setForm({ ...form, search_text: e.target.value })}
                required
              />
            </div>
          </div>

          {/* ── Categories / Platforms ────────────────────── */}
          <div className="grid gap-4 md:grid-cols-2">
            <MultiSelect
              label="Categories"
              options={categories}
              selected={form.categories as number[]}
              onChange={(selected) => setForm({ ...form, categories: selected })}
              placeholder="Select categories..."
            />
            <MultiSelect
              label="Platform IDs"
              options={platforms}
              selected={form.platform_ids as number[]}
              onChange={(selected) => setForm({ ...form, platform_ids: selected })}
              placeholder="Select platforms..."
            />
          </div>

          {/* ── Numeric fields ────────────────────────────── */}
          <div className="grid gap-4 md:grid-cols-3">
            <NumberField label="Max pages" value={form.max_pages} onChange={(v) => setForm({ ...form, max_pages: v })} />
            <NumberField label="Per page" value={form.per_page} onChange={(v) => setForm({ ...form, per_page: v })} />
            <NumberField label="Delay (seconds)" value={form.delay} onChange={(v) => setForm({ ...form, delay: v })} />
          </div>

          {/* ── Order ─────────────────────────────────────── */}
          <div className="grid gap-2">
            <Label htmlFor="order">Sort order</Label>
            <Select
              value={form.order || ""}
              onValueChange={(v) => setForm({ ...form, order: v || "" })}
            >
              <SelectTrigger id="order">
                <SelectValue placeholder="Default order" />
              </SelectTrigger>
              <SelectContent>
                {ORDER_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* ── Switches ──────────────────────────────────── */}
          <div className="grid gap-4 md:grid-cols-2">
            <SwitchField
              label="Config active"
              description="Enable/disable this scheduled job."
              checked={form.is_active}
              onCheckedChange={(v) => setForm({ ...form, is_active: v })}
            />
            <SwitchField
              label="Use proxy"
              description="Disable to connect directly (recommended in most cases)."
              checked={form.use_proxy}
              onCheckedChange={(v) => setForm({ ...form, use_proxy: v })}
            />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <SwitchField
              label="Fetch details"
              description="Fetch each listing detail page (richer data)."
              checked={form.fetch_details}
              onCheckedChange={(v) => setForm({ ...form, fetch_details: v })}
            />
            <SwitchField
              label="Details for new only"
              description="Only fetch details for new listings (not updates)."
              checked={form.details_for_new_only}
              onCheckedChange={(v) => setForm({ ...form, details_for_new_only: v })}
            />
          </div>

          {/* ── Detail Fetching Options ───────────────────── */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="grid gap-2">
              <Label htmlFor="details_strategy">Details Strategy</Label>
              <Select
                value={form.details_strategy}
                onValueChange={(v) => setForm({ ...form, details_strategy: v as "browser" | "http" })}
              >
                <SelectTrigger id="details_strategy">
                  <SelectValue placeholder="Select strategy" />
                </SelectTrigger>
                <SelectContent>
                  {DETAIL_STRATEGY_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <NumberField
              label="Details Concurrency"
              value={form.details_concurrency}
              onChange={(v) => setForm({ ...form, details_concurrency: v })}
              description="Number of concurrent detail fetches."
            />
          </div>

          {/* ── Error Handling ────────────────────────────── */}
          <div className="grid gap-4 md:grid-cols-2">
            <NumberField
              label="Error wait (minutes)"
              value={form.error_wait_minutes}
              onChange={(v) => setForm({ ...form, error_wait_minutes: v })}
              description="Minutes to wait on 403 errors."
            />
            <NumberField
              label="Max retries"
              value={form.max_retries}
              onChange={(v) => setForm({ ...form, max_retries: v })}
              description="Maximum retry attempts per page."
            />
          </div>

          {/* ── Advanced fields ───────────────────────────── */}
          <div className="grid gap-2">
            <Label htmlFor="base_url">Base URL (optional)</Label>
            <Input
              id="base_url"
              value={form.base_url}
              onChange={(e) => setForm({ ...form, base_url: e.target.value })}
              placeholder="https://www.vinted.sk/catalog"
            />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="grid gap-2">
              <Label htmlFor="locales">Locales (optional)</Label>
              <Input
                id="locales"
                value={form.locales}
                onChange={(e) => setForm({ ...form, locales: e.target.value })}
                placeholder="sk,en,pl"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="healthcheck_ping_url">Healthcheck URL (optional)</Label>
              <Input
                id="healthcheck_ping_url"
                value={form.healthcheck_ping_url}
                onChange={(e) => setForm({ ...form, healthcheck_ping_url: e.target.value })}
                placeholder="https://hc-ping.com/..."
              />
            </div>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="extra_filters">Extra filters (optional)</Label>
            <Textarea
              id="extra_filters"
              value={form.extra_filters}
              onChange={(e) => setForm({ ...form, extra_filters: e.target.value })}
              placeholder="color_ids[]=1&size_ids[]=207"
              rows={2}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="extra_args">Extra CLI arguments (optional)</Label>
            <Textarea
              id="extra_args"
              value={form.extra_args}
              onChange={(e) => setForm({ ...form, extra_args: e.target.value })}
              placeholder="--verbose --log-file /tmp/scraper.log"
              rows={2}
            />
          </div>

          {/* ── Cron schedule ─────────────────────────────── */}
          <div className="grid gap-2">
            <Label>Cron schedule</Label>
            <CronScheduler
              value={form.cron_schedule}
              onChange={(v) => setForm({ ...form, cron_schedule: v })}
            />
          </div>

          {/* ── Cron preview ─────────────────────────────── */}
          <div className="grid gap-3">
            <Label>Cron command preview</Label>
            <div className="flex flex-wrap items-center gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={handlePreview}
                disabled={previewLoading}
              >
                {previewLoading ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="size-4 animate-spin" /> Building...
                  </span>
                ) : (
                  "Preview command"
                )}
              </Button>
              {previewError && <span className="text-sm text-destructive">{previewError}</span>}
            </div>
            {preview && (
              <div className="relative">
                <pre className="max-h-48 overflow-auto rounded-md border bg-muted p-3 text-xs font-mono whitespace-pre-wrap">
                  {preview.command}
                  {preview.schedule ? `\n# schedule: ${preview.schedule}` : ""}
                </pre>
                <Button
                  type="button"
                  size="icon-sm"
                  variant="secondary"
                  className="absolute right-2 top-2"
                  onClick={handleCopyPreview}
                >
                  <Copy className="size-4" />
                </Button>
              </div>
            )}
          </div>

          {/* ── Footer ───────────────────────────────────── */}
          <DialogFooter className="flex flex-col gap-3 sm:flex-row sm:justify-end">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isSaving}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSaving}>
              {isSaving ? <Loader2 className="size-4 animate-spin" /> : "Save configuration"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
