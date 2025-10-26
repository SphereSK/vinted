"use client";

import { TableRow, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ListingAvatar } from "../common/ListingAvatar";
import { PriceChangeBadge } from "../common/PriceChangeBadge";
import { formatCurrency, formatDate, formatActiveDuration } from "@/lib/format";
import type { ListingResponse } from "@/lib/types";

interface ListingRowProps {
  listing: ListingResponse;
  platformLookup: Map<number, string>;
}

export function ListingRow({ listing, platformLookup }: ListingRowProps) {
  return (
    <TableRow>
      <TableCell className="flex items-center gap-3">
        <ListingAvatar listing={listing} />
        <div className="flex flex-col">
          <span className="font-medium">{listing.title}</span>
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
          {listing.condition_label && <Badge variant="secondary">{listing.condition_label}</Badge>}
        </div>
      </TableCell>

      <TableCell>
        <div className="flex flex-wrap gap-1">
          {listing.platform_names?.map((platform) => (
            <Badge key={platform} variant="secondary">{platform}</Badge>
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
