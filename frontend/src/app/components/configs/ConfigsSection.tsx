"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Play, Pencil, Trash2 } from "lucide-react";
import { toast } from "sonner";

import type { ScrapeConfigResponse, RuntimeStatusResponse } from "@/lib/types";
import { StatusBadge } from "../common/StatusBadge";
import { formatDate, formatDelaySeconds, formatProxyFlag } from "@/lib/format";

interface ConfigsSectionProps {
  configs: ScrapeConfigResponse[];
  statuses: Record<number, RuntimeStatusResponse | null>;
  onEdit: (config: ScrapeConfigResponse) => void;
  onRun?: (config: ScrapeConfigResponse) => Promise<void> | void;
  onDelete?: (config: ScrapeConfigResponse) => Promise<void> | void;
}

export function ConfigsSection({
  configs,
  statuses,
  onEdit,
  onRun,
  onDelete,
}: ConfigsSectionProps) {
  if (!configs.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Scrape configurations</CardTitle>
          <CardDescription>
            Manage search parameters, scheduler settings, and trigger manual runs.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No configurations yet — create your first via “New config”.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Scrape configurations</CardTitle>
        <CardDescription>
          Manage search parameters, scheduler settings, and trigger manual runs.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Search text</TableHead>
              <TableHead>Schedule</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-48">Last run</TableHead>
              <TableHead className="w-[160px]" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {configs.map((config) => (
              <TableRow key={config.id}>
                <TableCell>
                  <div className="flex flex-col">
                    <span className="font-medium">{config.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {config.is_active ? "Active" : "Inactive"} · {config.max_pages} pages · delay {formatDelaySeconds(config.delay)}s
                    </span>
                    <span className="text-xs text-muted-foreground">
                      Proxy {formatProxyFlag(config.use_proxy)} · Strategy {config.details_strategy ?? "browser"}
                    </span>
                  </div>
                </TableCell>
                <TableCell className="max-w-[220px]">
                  <span className="line-clamp-2 text-sm">
                    {config.search_text}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    Order: {config.order ?? "default"}
                  </span>
                  {config.base_url && (
                    <span className="text-xs text-muted-foreground">
                      Base URL: {config.base_url}
                    </span>
                  )}
                </TableCell>
                <TableCell className="text-sm">
                  {config.cron_schedule ?? "Manual"}
                </TableCell>
                <TableCell>
                  <StatusBadge status={statuses[config.id]} />
                </TableCell>
                <TableCell className="text-sm">
                  {config.last_run_at ? (
                    <div className="flex flex-col">
                      <span>{formatDate(config.last_run_at)}</span>
                      {typeof config.last_run_items === "number" && (
                        <span className="text-xs text-muted-foreground">
                          {config.last_run_items} items scraped
                        </span>
                      )}
                    </div>
                  ) : (
                    <span className="text-muted-foreground text-sm">Never run</span>
                  )}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    {onRun && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => void onRun(config)}
                      >
                        <Play className="size-4" /> Run
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => onEdit(config)}
                    >
                      <Pencil className="size-4" />
                    </Button>
                    {onDelete && (
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        className="text-destructive hover:bg-destructive/10"
                        onClick={() => void onDelete(config)}
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

