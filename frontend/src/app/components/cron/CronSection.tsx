import { useMemo } from "react";
import { Copy, Loader2, Repeat, RefreshCcw } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { CronJobEntry, ScrapeConfigResponse } from "@/lib/types";

interface CronSectionProps {
  jobs: CronJobEntry[];
  configs: ScrapeConfigResponse[];
  loading: boolean;
  syncing: boolean;
  error: Error | null;
  onReload: () => void | Promise<void>;
  onSync: () => void | Promise<void>;
}

export function CronSection({
  jobs,
  configs,
  loading,
  syncing,
  error,
  onReload,
  onSync,
}: CronSectionProps) {
  const configLookup = useMemo(() => {
    const map = new Map<number, ScrapeConfigResponse>();
    configs.forEach((cfg) => {
      map.set(cfg.id, cfg);
    });
    return map;
  }, [configs]);

  async function handleCopy(command: string) {
    if (!command) return;
    if (typeof navigator === "undefined" || !navigator.clipboard) {
      toast.error("Clipboard API not available in this environment.");
      return;
    }
    try {
      await navigator.clipboard.writeText(command);
      toast.success("Cron command copied to clipboard");
    } catch (copyError) {
      const message =
        copyError instanceof Error
          ? copyError.message
          : "Unable to access clipboard";
      toast.error("Failed to copy cron command", { description: message });
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <CardTitle>Cron scheduler</CardTitle>
          <CardDescription>
            View scheduled scrape jobs and keep the system crontab in sync.
          </CardDescription>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            onClick={() => {
              void onSync();
            }}
            disabled={syncing}
          >
            {syncing ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Repeat className="size-4" />
            )}
            Sync cron
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              void onReload();
            }}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <RefreshCcw className="size-4" />
            )}
            Refresh list
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center gap-2 py-10 text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading cron jobs…
          </div>
        ) : error ? (
          <p className="text-sm text-destructive">{error}</p>
        ) : jobs.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No cron jobs configured yet. Use sync to pull active schedules.
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[120px]">Schedule</TableHead>
                <TableHead>Configuration</TableHead>
                <TableHead>Command</TableHead>
                <TableHead className="w-[120px]">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {jobs.map((job, index) => {
                const config =
                  job.config_id != null
                    ? configLookup.get(job.config_id)
                    : undefined;
                const configLabel = config
                  ? config.name
                  : job.config_id != null
                    ? `Config #${job.config_id}`
                    : "Manual entry";

                return (
                  <TableRow key={`${job.comment ?? job.command}-${index}`}>
                    <TableCell className="align-top font-mono text-xs">
                      {job.schedule}
                    </TableCell>
                    <TableCell className="align-top">
                      <div className="flex flex-col">
                        <span className="font-medium">{configLabel}</span>
                        {job.comment ? (
                          <span className="text-xs text-muted-foreground">
                            {job.comment}
                          </span>
                        ) : null}
                      </div>
                    </TableCell>
                    <TableCell className="align-top">
                      <div className="flex items-start gap-2">
                        <pre className="max-h-32 flex-1 overflow-auto rounded-md border bg-muted px-2 py-1 text-xs font-mono whitespace-pre-wrap">
                          {job.command}
                        </pre>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon-sm"
                          aria-label="Copy cron command"
                          onClick={() => {
                            void handleCopy(job.command);
                          }}
                        >
                          <Copy className="size-4" />
                        </Button>
                      </div>
                    </TableCell>
                    <TableCell className="align-top">
                      <Badge
                        className={
                          job.enabled
                            ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-500"
                            : "bg-muted text-muted-foreground"
                        }
                      >
                        {job.enabled ? "Enabled" : "Disabled"}
                      </Badge>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
