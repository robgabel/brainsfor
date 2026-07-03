// In-memory sliding-window rate limiter used ONLY when Upstash is unreachable.
// Per-instance (not shared across lambdas), so it's a weaker guarantee than
// Redis — but it turns "Upstash outage = unlimited Anthropic spend" into
// "Upstash outage = per-instance limits," which is strictly better than the
// old fail-open behavior while still keeping the demo alive.

const buckets = new Map<string, number[]>();
const WINDOW_MS = 24 * 60 * 60 * 1000;

export function fallbackRateLimit(
  key: string,
  limit: number,
): { allowed: boolean; remaining: number } {
  const now = Date.now();
  const cutoff = now - WINDOW_MS;
  const hits = (buckets.get(key) ?? []).filter((t) => t > cutoff);
  if (hits.length >= limit) {
    buckets.set(key, hits);
    return { allowed: false, remaining: 0 };
  }
  hits.push(now);
  buckets.set(key, hits);
  // Opportunistic cleanup so an attacker rotating IPs can't grow the map forever.
  if (buckets.size > 10_000) {
    for (const [k, v] of buckets) {
      if (v.every((t) => t <= cutoff)) buckets.delete(k);
    }
  }
  return { allowed: true, remaining: limit - hits.length };
}
