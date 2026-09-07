import type { APIError, Claim, EligibilityResponse, Transaction } from "./types";

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
const proxyPath = "/api/claimguard";

export class ClaimGuardApiError extends Error {
  constructor(public readonly code: string, message: string) {
    super(message);
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  if (!baseUrl) {
    throw new ClaimGuardApiError(
      "API_CONFIGURATION_ERROR",
      "ClaimGuard is not connected yet. Set NEXT_PUBLIC_API_BASE_URL to continue.",
    );
  }

  let response: Response;
  try {
    response = await fetch(`${proxyPath}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...options?.headers },
    });
  } catch {
    throw new ClaimGuardApiError(
      "NETWORK_ERROR",
      "We couldn't reach ClaimGuard. Please try again in a moment.",
    );
  }

  if (!response.ok) {
    const error = (await response.json().catch(() => null)) as APIError | null;
    throw new ClaimGuardApiError(
      error?.code ?? "SERVER_ERROR",
      error?.message ?? "Something went wrong. Please try again.",
    );
  }

  return response.json() as Promise<T>;
}

export const api = {
  getTransactions: () => request<Transaction[]>("/transactions"),
  getClaims: () => request<Claim[]>("/claims"),
  getClaim: (claimId: string) => request<Claim>(`/claims/${claimId}`),
  getEligibility: (transactionId: string) =>
    request<EligibilityResponse>(`/transactions/${transactionId}/eligibility`),
  startClaim: (transactionId: string) =>
    request<Claim>(`/transactions/${transactionId}/claim`, { method: "POST" }),
};
