import { NextRequest, NextResponse } from "next/server";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "");

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

async function proxy(request: NextRequest, context: RouteContext) {
  if (!apiBaseUrl) {
    return NextResponse.json(
      {
        code: "API_CONFIGURATION_ERROR",
        message: "ClaimGuard is not connected yet.",
      },
      { status: 500 },
    );
  }

  const { path } = await context.params;
  const upstreamUrl = new URL(`${apiBaseUrl}/${path.join("/")}`);
  upstreamUrl.search = request.nextUrl.search;
  const requestBody = request.method === "POST" ? await request.text() : undefined;

  try {
    const upstreamResponse = await fetch(upstreamUrl, {
      method: request.method,
      headers: {
        "Content-Type": request.headers.get("Content-Type") ?? "application/json",
      },
      body: requestBody || undefined,
      cache: "no-store",
    });

    return new NextResponse(upstreamResponse.body, {
      status: upstreamResponse.status,
      headers: {
        "Content-Type": upstreamResponse.headers.get("Content-Type") ?? "application/json",
      },
    });
  } catch {
    return NextResponse.json(
      {
        code: "UPSTREAM_UNAVAILABLE",
        message: "ClaimGuard is temporarily unavailable. Please try again.",
      },
      { status: 502 },
    );
  }
}

export async function GET(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export async function POST(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}
