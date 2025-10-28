"use client";

import { useState } from "react";
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
import { Play, Pencil, Trash2, Copy, Power, PowerOff, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";

import type { ScrapeConfigResponse, RuntimeStatusResponse } from "@/lib/types";
import { StatusBadge } from "../common/StatusBadge";
import { formatDate, formatDelaySeconds, formatProxyFlag } from "@/lib/format";

interface ConfigsSectionProps {
  configs: ScrapeConfigResponse[];
  statuses: Record<number, RuntimeStatusResponse | null>;
  onEdit: (config: ScrapeConfigResponse) => void;
  onCopy?: (config: ScrapeConfigResponse) => void;
  onRun?: (config: ScrapeConfigResponse) => Promise<void> | void;
  onDelete?: (config: ScrapeConfigResponse) => Promise<void> | void;
  onToggleActive?: (config: ScrapeConfigResponse, newActiveState: boolean) => Promise<void> | void;
}

export function ConfigsSection({
  configs,
  statuses,
  onEdit,
  onCopy,
  onRun,
  onDelete,
  onToggleActive,
}: ConfigsSectionProps) {
  console.log("ConfigsSection received configs:", configs);

  // Track loading states for each action type per config
  const [loadingStates, setLoadingStates] = useState<Record<number, {
    running?: boolean;
    copying?: boolean;
    deleting?: boolean;
    toggling?: boolean;
  }>>({});

  const handleRunWithLoading = async (config: ScrapeConfigResponse) => {
    if (!onRun) return;
    setLoadingStates((prev) => ({ ...prev, [config.id]: { ...prev[config.id], running: true } }));
    try {
      await onRun(config);
    } finally {
      setLoadingStates((prev) => ({ ...prev, [config.id]: { ...prev[config.id], running: false } }));
    }
  };

  const handleCopyWithLoading = async (config: ScrapeConfigResponse) => {
    if (!onCopy) return;
    setLoadingStates((prev) => ({ ...prev, [config.id]: { ...prev[config.id], copying: true } }));
    try {
      await onCopy(config);
    } finally {
      setLoadingStates((prev) => ({ ...prev, [config.id]: { ...prev[config.id], copying: false } }));
    }
  };

  const handleDeleteWithLoading = async (config: ScrapeConfigResponse) => {
    if (!onDelete) return;
    setLoadingStates((prev) => ({ ...prev, [config.id]: { ...prev[config.id], deleting: true } }));
    try {
      await onDelete(config);
    } finally {
      setLoadingStates((prev) => ({ ...prev, [config.id]: { ...prev[config.id], deleting: false } }));
    }
  };

  const handleToggleWithLoading = async (config: ScrapeConfigResponse, newActiveState: boolean) => {
    if (!onToggleActive) return;
    setLoadingStates((prev) => ({ ...prev, [config.id]: { ...prev[config.id], toggling: true } }));
    try {
      await onToggleActive(config, newActiveState);
    } finally {
      setLoadingStates((prev) => ({ ...prev, [config.id]: { ...prev[config.id], toggling: false } }));
    }
  };

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
              <TableHead>Active</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-48">Last run</TableHead>
              <TableHead className="w-[160px]" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {configs.map((config) => (
              <TableRow key={config.id} className={!config.is_active ? "opacity-60" : ""}>
                <TableCell>
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{config.name}</span>
                      <Badge
                        variant={config.is_active ? "default" : "secondary"}
                        className={config.is_active ? "bg-green-500 hover:bg-green-600" : ""}
                      >
                        {config.is_active ? (
                          <><Power className="size-3 mr-1" /> Active</>
                        ) : (
                          <><PowerOff className="size-3 mr-1" /> Inactive</>
                        )}
                      </Badge>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {config.max_pages} pages · delay {formatDelaySeconds(config.delay)}s
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
                  {onToggleActive ? (
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={config.is_active}
                        onCheckedChange={(checked) => void handleToggleWithLoading(config, checked)}
                        disabled={loadingStates[config.id]?.toggling}
                        title={config.is_active ? "Disable configuration" : "Enable configuration"}
                      />
                      {loadingStates[config.id]?.toggling && (
                        <Loader2 className="size-4 animate-spin text-muted-foreground" />
                      )}
                    </div>
                  ) : (
                    <span className="text-sm text-muted-foreground">
                      {config.is_active ? "Enabled" : "Disabled"}
                    </span>
                  )}
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
                        onClick={() => void handleRunWithLoading(config)}
                        disabled={loadingStates[config.id]?.running}
                      >
                        {loadingStates[config.id]?.running ? (
                          <>
                            <Loader2 className="size-4 animate-spin" /> Running...
                          </>
                        ) : (
                          <>
                            <Play className="size-4" /> Run
                          </>
                        )}
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => onEdit(config)}
                      title="Edit configuration"
                    >
                      <Pencil className="size-4" />
                    </Button>
                    {onCopy && (
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => void handleCopyWithLoading(config)}
                        disabled={loadingStates[config.id]?.copying}
                        title="Copy configuration"
                      >
                        {loadingStates[config.id]?.copying ? (
                          <Loader2 className="size-4 animate-spin" />
                        ) : (
                          <Copy className="size-4" />
                        )}
                      </Button>
                    )}
                    {onDelete && (
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        className="text-destructive hover:bg-destructive/10"
                        onClick={() => void handleDeleteWithLoading(config)}
                        disabled={loadingStates[config.id]?.deleting}
                        title="Delete configuration"
                      >
                        {loadingStates[config.id]?.deleting ? (
                          <Loader2 className="size-4 animate-spin" />
                        ) : (
                          <Trash2 className="size-4" />
                        )}
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

