export const config = { runtime: "edge" };

declare const process: {
  env: Record<string, string | undefined>;
};

type HeadersInit = Record<string, string>;

const cloneContentHeaders = (headers: Headers): HeadersInit => {
  const allowed = new Set(["content-type", "content-length", "cache-control", "etag"]);
  const result: HeadersInit = {};
  for (const [key, value] of headers.entries()) {
    if (allowed.has(key.toLowerCase())) {
      result[key] = value;
    }
  }
  if (!result["content-type"]) {
    const contentType = headers.get("content-type");
    if (contentType) {
      result["content-type"] = contentType;
    }
  }
  return result;
};

export default async function handler(req: Request): Promise<Response> {
  const backendBase = process.env.BACKEND_BASE;
  if (!backendBase) {
    return new Response("BACKEND_BASE is not configured", { status: 500 });
  }

  if (req.method !== "GET" && req.method !== "HEAD") {
    return new Response("Method not allowed", { status: 405 });
  }

  const requestUrl = new URL(req.url);
  const targetUrl = `${backendBase.replace(/\/$/, "")}/search${requestUrl.search}`;

  const upstreamResponse = await fetch(targetUrl, {
    method: "GET",
    headers: req.headers,
  });

  const body = await upstreamResponse.text();
  const headers = cloneContentHeaders(upstreamResponse.headers);

  return new Response(body, {
    status: upstreamResponse.status,
    headers,
  });
}
