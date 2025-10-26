"use client";

import { TableRow, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ListingAvatar } from "../common/ListingAvatar";
import { PriceChangeBadge } from "../common/PriceChangeBadge";
import { formatCurrency, formatDate, formatActiveDuration } from "@/lib/format";
import type { ListingResponse } from "@/lib/types";

import type { BadgeProps } from "@/components/ui/badge";

interface ListingRowProps {
  listing: ListingResponse;
  platformLookup: Map<number, string>;
  getConditionBadgeVariant: (condition: string | null) => BadgeProps["variant"];
  getPlatformBadgeVariant: (platform: string | null) => BadgeProps["variant"];
}

export function ListingRow({ listing, platformLookup, getConditionBadgeVariant, getPlatformBadgeVariant }: ListingRowProps) {
  return (
    <TableRow>
      <TableCell className="flex items-center gap-3">
        <ListingAvatar listing={listing} />
        <div className="flex flex-col">
          <a href={listing.url} target="_blank" rel="noopener noreferrer" className="font-medium hover:underline">
            {listing.title}
          </a>
          <span className="text-xs text-muted-foreground">#{listing.id}</span>
        </div>
      </TableCell>

      <TableCell className="text-sm">
        {listing.price_cents
          ? formatCurrency(listing.price_cents, listing.currency)
          : "—"}
      </TableCell>

      <TableCell>
        <PriceChangeBadge
          change={listing.price_change}
          current={listing.price_cents}
          previous={listing.previous_price_cents}
          currency={listing.currency}
        />
      </TableCell>

      <TableCell>
        <div className="flex flex-wrap gap-1">
          {listing.condition_label && <Badge variant={getConditionBadgeVariant(listing.condition_label)}>{listing.condition_label}</Badge>}
        </div>
      </TableCell>

      <TableCell>
        <div className="flex flex-wrap gap-1">
          {listing.platform_names?.map((platform) => (
            <Badge key={platform} variant={getPlatformBadgeVariant(platform)}>{platform}</Badge>
          ))}
        </div>
      </TableCell>

      <TableCell>
        <div className="flex flex-wrap gap-1">
          {listing.source_label && <Badge variant="secondary">{listing.source_label}</Badge>}
        </div>
      </TableCell>

      <TableCell className="text-xs text-muted-foreground">
        {formatDate(listing.last_seen_at)}
      </TableCell>

      <TableCell className="text-xs text-muted-foreground">
        {formatDate(listing.first_seen_at)}
      </TableCell>

      <TableCell className="text-xs text-muted-foreground">
        {formatActiveDuration(listing.first_seen_at)}
      </TableCell>
    </TableRow>
  );
}
