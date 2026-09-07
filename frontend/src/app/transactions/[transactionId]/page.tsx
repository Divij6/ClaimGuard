"use client";

import { CheckCircle2, CircleAlert, Copy, ExternalLink, LoaderCircle } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, ClaimGuardApiError } from "@/lib/api";
import { formatBenefit, formatMoney } from "@/lib/format";
import type { Claim, EligibilityResponse } from "@/lib/types";
import { LoadingButton, PageSkeleton } from "@/components/ui";

export default function TransactionDetailsPage() {
  const params = useParams<{ transactionId: string }>();
  const transactionId = params.transactionId;
  const [eligibility, setEligibility] = useState<EligibilityResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [claim, setClaim] = useState<Claim | null>(null);

  useEffect(() => { api.getEligibility(transactionId).then(setEligibility).catch((cause: unknown) => setError(readError(cause))).finally(() => setLoading(false)); }, [transactionId]);

  async function startClaim() {
    setStarting(true); setError("");
    try { setClaim(await api.startClaim(transactionId)); } catch (cause) { setError(readError(cause)); } finally { setStarting(false); }
  }

  if (loading) return <PageSkeleton />;
  if (error && !eligibility) return <ErrorPanel message={error} />;
  if (!eligibility) return null;

  return <div className="mx-auto max-w-3xl space-y-6"><Link href="/" className="text-sm font-semibold text-accent hover:text-[#0A6045]">← Back to dashboard</Link><header><p className="text-sm font-semibold text-accent">Transaction review</p><h1 className="mt-2 text-3xl font-semibold tracking-tight">Coverage decision</h1></header><section className="rounded-2xl border border-line bg-white p-6 shadow-card"><p className="text-xs font-semibold uppercase tracking-[.1em] text-[#778079]">Transaction ID</p><div className="mt-2 flex items-center gap-2"><code className="min-w-0 truncate text-sm font-medium">{transactionId}</code><Copy size={15} className="shrink-0 text-[#8B938D]" /></div><p className="mt-5 text-sm leading-6 text-[#66706A]">Merchant, amount, currency, and transaction date are not available from the current transaction APIs. ClaimGuard is showing the server-provided coverage decision for this ID.</p></section>{claim ? <SuccessCard claim={claim} /> : eligibility.eligible ? <EligibleCard eligibility={eligibility} starting={starting} onStart={startClaim} /> : <IneligibleCard eligibility={eligibility} />}{error && <p className="rounded-xl bg-[#FFF6E9] px-4 py-3 text-sm text-[#76521F]">{error}</p>}</div>;
}

function EligibleCard({ eligibility, starting, onStart }: { eligibility: EligibilityResponse; starting: boolean; onStart: () => void }) { return <section className="overflow-hidden rounded-2xl border border-[#BFE4D1] bg-white shadow-card"><div className="bg-accent-soft px-6 py-5"><p className="flex items-center gap-2 font-semibold text-accent"><CheckCircle2 size={19} /> You&apos;re eligible</p></div><div className="p-6 sm:p-8"><p className="text-lg font-semibold">{formatBenefit(eligibility.benefitType ?? "")}</p><p className="mt-6 text-sm font-medium text-[#66706A]">Potential benefit</p><p className="mt-1 text-5xl font-semibold tracking-tight text-accent tabular-nums">{formatMoney(eligibility.eligibleAmount)}</p><p className="mt-6 max-w-lg text-sm leading-6 text-[#66706A]">{eligibility.reason}</p><button onClick={onStart} disabled={starting} className="mt-7 inline-flex min-w-36 items-center justify-center rounded-xl bg-accent px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#0A6045] active:scale-[.98] disabled:cursor-not-allowed disabled:opacity-70">{starting ? <LoadingButton>Starting claim...</LoadingButton> : "Start claim"}</button></div></section>; }
function IneligibleCard({ eligibility }: { eligibility: EligibilityResponse }) { return <section className="rounded-2xl border border-line bg-white p-7 shadow-card"><p className="flex items-center gap-2 font-semibold text-[#56615A]"><CircleAlert size={19} /> Not eligible</p><h2 className="mt-6 text-2xl font-semibold tracking-tight">This transaction does not currently qualify for an available ClaimGuard benefit.</h2><div className="mt-6 rounded-xl bg-canvas p-4"><p className="text-xs font-semibold uppercase tracking-[.08em] text-[#778079]">Reason</p><p className="mt-2 text-sm leading-6 text-[#56615A]">{eligibility.reason}</p></div></section>; }
function SuccessCard({ claim }: { claim: Claim }) { return <section className="rounded-2xl border border-[#BFE4D1] bg-white p-7 shadow-card"><p className="flex items-center gap-2 font-semibold text-accent"><CheckCircle2 size={19} /> Claim started</p><h2 className="mt-6 text-2xl font-semibold">{formatBenefit(claim.benefit_type)}</h2><p className="mt-1 text-4xl font-semibold tracking-tight text-accent tabular-nums">{formatMoney(claim.amount)}</p><p className="mt-5 text-sm text-[#66706A]">Your ClaimGuard claim has been created.</p><Link href={`/claims/${claim.id}`} className="mt-7 inline-flex items-center gap-2 rounded-xl bg-accent px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#0A6045]"><ExternalLink size={16} /> View claim</Link></section>; }
function ErrorPanel({ message }: { message: string }) { return <div className="mx-auto max-w-xl rounded-2xl border border-line bg-white p-10 text-center shadow-card"><CircleAlert className="mx-auto text-[#8B938D]" /><h1 className="mt-4 text-xl font-semibold">Transaction unavailable</h1><p className="mt-2 text-sm leading-6 text-[#66706A]">{message}</p><Link className="mt-6 inline-block text-sm font-semibold text-accent" href="/">Back to dashboard</Link></div>; }
function readError(cause: unknown): string { if (cause instanceof ClaimGuardApiError) { if (cause.code === "TRANSACTION_NOT_FOUND") return "Transaction not found."; if (cause.code === "CLAIM_ALREADY_EXISTS") return "This claim has already been started."; if (cause.code === "TRANSACTION_NOT_ELIGIBLE") return "This transaction is not eligible for a claim."; return cause.message; } return "Something went wrong. Please try again."; }
