export const config = { runtime: "edge" };

declare const process: {
  env: Record<string, string | undefined>;
};

type HeadersInit = Record<string, string>;

const sanitizeContentHeaders = (headers: Headers): HeadersInit => {
  const allowed = new Set(["content-type", "cache-control", "etag"]);
  const result: HeadersInit = {};
  for (const [key, value] of headers.entries()) {
    if (allowed.has(key.toLowerCase())) {
      result[key] = value;
    }
  }
  const contentType = headers.get("content-type");
  if (contentType) {
    result["content-type"] = contentType;
  }
  return result;
};

export default async function handler(req: Request): Promise<Response> {
  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  const backendBase = process.env.BACKEND_BASE;
  if (!backendBase) {
    return new Response("BACKEND_BASE is not configured", { status: 500 });
  }

  const sanitizedBase = backendBase.replace(/\/$/, "");
  const targetUrl = `${sanitizedBase}/analyze/listings`;

  const bodyText = await req.text().catch(() => "{}");
  const headers = new Headers(req.headers);
  if (!headers.has("content-type")) {
    headers.set("content-type", "application/json");
  }

  const upstreamResponse = await fetch(targetUrl, {
    method: "POST",
    headers,
    body: bodyText || "{}",
  });

  const responseBody = await upstreamResponse.text();
  const responseHeaders = sanitizeContentHeaders(upstreamResponse.headers);

  return new Response(responseBody, {
    status: upstreamResponse.status,
    headers: responseHeaders,
  });
}
