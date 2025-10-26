import { Buffer } from "node:buffer";

import { NextRequest, NextResponse } from "next/server";

const upstreamBaseUrl =
  process.env.FASTAPI_INTERNAL_URL?.replace(/\/$/, "") ??
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8933";

const apiKeyHeader =
  process.env.FASTAPI_API_KEY_HEADER ??
  process.env.NEXT_PUBLIC_API_KEY_HEADER ??
  "X-API-Key";

const apiKeyValue =
  process.env.FASTAPI_API_KEY ?? process.env.NEXT_PUBLIC_API_KEY ?? "";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type RouteParams = {
  params: { path?: string[] } | Promise<{ path?: string[] }>;
};

async function resolveParams(
  params: { path?: string[] } | Promise<{ path?: string[] }>,
): Promise<{ path?: string[] } | undefined> {
  if (typeof (params as Promise<unknown>)?.then === "function") {
    return (params as Promise<{ path?: string[] }>).catch(() => undefined);
  }
  return params as { path?: string[] };
}

async function proxyRequest(
  request: NextRequest,
  context: RouteParams | Promise<RouteParams>,
) {
  const resolvedContext = await Promise.resolve(context);
  const resolvedParams = await resolveParams(resolvedContext.params);
  const pathSegments = resolvedParams?.path ?? [];

  if (!upstreamBaseUrl) {
    return NextResponse.json(
      { detail: "FASTAPI backend is not configured." },
      { status: 500 },
    );
  }

  if (request.method === "OPTIONS") {
    return new NextResponse(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin":
          request.headers.get("origin") ?? "*",
        "Access-Control-Allow-Methods":
          request.headers.get("access-control-request-method") ??
          "GET,POST,PUT,DELETE,OPTIONS",
        "Access-Control-Allow-Headers":
          request.headers.get("access-control-request-headers") ?? "*",
      },
    });
  }

  const suffix = pathSegments.join("/");
  const targetUrl = new URL(
    suffix ? `${upstreamBaseUrl}/${suffix}` : upstreamBaseUrl,
  );

  if (request.nextUrl.search) {
    targetUrl.search = request.nextUrl.search;
  }

  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("content-length");
  headers.delete("connection");

  if (apiKeyValue && !headers.has(apiKeyHeader)) {
    headers.set(apiKeyHeader, apiKeyValue);
  }

  let body: BodyInit | null = null;
  if (!["GET", "HEAD"].includes(request.method.toUpperCase())) {
    const buffer = await request.arrayBuffer();
    body = Buffer.from(buffer);
  }

  let upstreamResponse: Response;
  try {
    upstreamResponse = await fetch(targetUrl.toString(), {
      method: request.method,
      headers,
      body,
      redirect: "manual",
    });
  } catch (error) {
    console.error("Proxy request failed:", error);
    return NextResponse.json(
      { detail: "Unable to reach FastAPI backend." },
      { status: 502 },
    );
  }

  const responseHeaders = new Headers(upstreamResponse.headers);
  responseHeaders.delete("content-length");
  responseHeaders.set("Access-Control-Allow-Origin", "*");

  return new NextResponse(upstreamResponse.body, {
    status: upstreamResponse.status,
    headers: responseHeaders,
  });
}

export { proxyRequest as GET };
export { proxyRequest as POST };
export { proxyRequest as PUT };
export { proxyRequest as DELETE };
export { proxyRequest as PATCH };
export { proxyRequest as HEAD };
export { proxyRequest as OPTIONS };
