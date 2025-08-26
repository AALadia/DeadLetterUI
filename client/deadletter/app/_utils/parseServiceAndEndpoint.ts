/**
 * Parse a service name (from subdomain) and endpoint (last path segment)
 * from a URL or host/path string.
 *
 * Examples:
 *  - "https://accounting-376095984666.asia-east1.run.app/receiveTransactionCreatePayment"
 *      -> { service: "accounting", endpoint: "receiveTransactionCreatePayment" }
 *  - "accounting-376095984666.asia-east1.run.app/receiveTransactionCreatePayment"
 *      -> { service: "accounting", endpoint: "receiveTransactionCreatePayment" }
 *  - "/receiveTransactionCreatePayment"
 *      -> { service: null, endpoint: "receiveTransactionCreatePayment" }
 */
export function parseServiceAndEndpoint(input: string): {
  service: string | null;
  endpoint: string | null;
} {
  // Try to coerce into a URL first
  try {
    const normalized = input.includes("://") ? input : `https://${input}`;
    const url = new URL(normalized);

    // service: first hostname label, before any "-" suffixes (e.g., "accounting-123" -> "accounting")
    const firstLabel = url.hostname.split(".")[0] ?? "";
    const service =
      firstLabel.includes("-") ? firstLabel.split("-")[0] : firstLabel || null;

    // endpoint: last non-empty segment of the path
    const pathParts = url.pathname.split("/").filter(Boolean);
    const endpoint = (pathParts.at(-1) ?? null) || null;

    return { service, endpoint };
  } catch {
    // Fallback for plain paths like "/receiveTransactionCreatePayment"
    const endpoint = input.split("/").filter(Boolean).pop() ?? null;
    return { service: null, endpoint };
  }
}

// --- Example usage ---
// const { service, endpoint } = parseServiceAndEndpoint(
//   "https://accounting-un.app/receiveTransactionCreatePayment"
// );
// service === "accounting"
// endpoint === "receiveTransactionCreatePayment"
