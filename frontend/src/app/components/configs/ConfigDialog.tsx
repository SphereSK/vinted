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
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { X, Loader2, Copy } from "lucide-react";
import { toast } from "sonner";

import type {
  ScrapeConfigResponse,
  ScrapeConfigWritePayload,
  CategoryResponse,
  CronCommandResponse,
} from "@/lib/types";
import { buildCronCommand } from "@/lib/endpoints";
import { useState } from "react";
import { NumberField } from "../common/NumberField";
import { SwitchField } from "../common/SwitchField";
import { HelperList } from "../common/HelperList";

const ORDER_OPTIONS = [
  { value: "newest_first", label: "Newest first" },
  { value: "price_low_to_high", label: "Price low → high" },
  { value: "price_high_to_low", label: "Price high → low" },
];

const DETAIL_STRATEGY_OPTIONS = [
  { value: "browser" as const, label: "Browser (Chromium)" },
  { value: "http" as const, label: "HTTP requests" },
];

const CRON_PRESETS = [
  { value: "0 * * * *", label: "Hourly" },
  { value: "0 */6 * * *", label: "Every 6 hours" },
  { value: "0 0 * * *", label: "Daily at midnight" },
  { value: "0 9 * * *", label: "Daily at 09:00" },
  { value: "0 18 * * 1-5", label: "Weekdays at 18:00" },
  { value: "*/30 * * * *", label: "Every 30 minutes" },
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
  // Local editable state based on incoming config
  const [form, setForm] = useState(() =>
    config
      ? { ...config }
      : {
          name: "",
          search_text: "",
          categories: "",
          platform_ids: "",
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

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (isSaving) return;
    setIsSaving(true);
    try {
      const payload: ScrapeConfigWritePayload = {
        ...form,
        name: form.name.trim(),
        search_text: form.search_text.trim(),
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
            <div className="grid gap-2">
              <Label htmlFor="categories">Categories (IDs)</Label>
              <Input
                id="categories"
                value={form.categories}
                onChange={(e) => setForm({ ...form, categories: e.target.value })}
                placeholder="3026,1953"
              />
              <HelperList items={categories} />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="platform_ids">Platform IDs</Label>
              <Input
                id="platform_ids"
                value={form.platform_ids}
                onChange={(e) => setForm({ ...form, platform_ids: e.target.value })}
                placeholder="1280,1281"
              />
              <HelperList items={platforms} />
            </div>
          </div>

          {/* ── Numeric fields ────────────────────────────── */}
          <div className="grid gap-4 md:grid-cols-3">
            <NumberField label="Max pages" value={form.max_pages} onChange={(v) => setForm({ ...form, max_pages: v })} />
            <NumberField label="Per page" value={form.per_page} onChange={(v) => setForm({ ...form, per_page: v })} />
            <NumberField label="Delay (seconds)" value={form.delay} onChange={(v) => setForm({ ...form, delay: v })} />
          </div>

          {/* ── Switches ──────────────────────────────────── */}
          <div className="grid gap-4 md:grid-cols-2">
            <SwitchField
              label="Fetch details"
              description="Fetch each listing detail page (richer data)."
              checked={form.fetch_details}
              onCheckedChange={(v) => setForm({ ...form, fetch_details: v })}
            />
            <SwitchField
              label="Use proxy"
              description="Disable to connect directly (recommended in most cases)."
              checked={form.use_proxy}
              onCheckedChange={(v) => setForm({ ...form, use_proxy: v })}
            />
          </div>

          {/* ── Cron schedule ─────────────────────────────── */}
          <div className="grid gap-2">
            <Label htmlFor="cron_schedule">Cron schedule</Label>
            <Select
              value={form.cron_schedule}
              onValueChange={(v) => setForm({ ...form, cron_schedule: v })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a preset" />
              </SelectTrigger>
              <SelectContent>
                {CRON_PRESETS.map((preset) => (
                  <SelectItem key={preset.value} value={preset.value}>
                    {preset.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
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
