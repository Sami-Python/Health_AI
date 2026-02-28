import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

/**
 * Custom fetch wrapper with retry logic for increased resilience.
 * Useful for handling temporary network blips or rate limits.
 */
export async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  retries: number = 3,
  backoff: number = 500
): Promise<Response> {
  try {
    const response = await fetch(url, options);

    // If success (2xx), return immediately
    if (response.ok) return response;

    // If we have retries left and it's a retryable error (e.g. 5xx or 429)
    if (retries > 0 && (response.status >= 500 || response.status === 429)) {
      console.warn(`Fetch failed with ${response.status}. Retrying in ${backoff}ms... (${retries} left)`);
      await new Promise(resolve => setTimeout(resolve, backoff));
      return fetchWithRetry(url, options, retries - 1, backoff * 2);
    }

    return response;
  } catch (error) {
    // Network errors (e.g. DNS, connection refused)
    if (retries > 0) {
      console.warn(`Fetch error: ${error}. Retrying in ${backoff}ms... (${retries} left)`);
      await new Promise(resolve => setTimeout(resolve, backoff));
      return fetchWithRetry(url, options, retries - 1, backoff * 2);
    }
    throw error;
  }
}
