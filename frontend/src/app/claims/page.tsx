"use client";

import { ArrowRight, FileCheck2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, ClaimGuardApiError } from "@/lib/api";
import { formatBenefit, formatDate, formatMoney } from "@/lib/format";
import type { Claim } from "@/lib/types";
import { PageSkeleton } from "@/components/ui";

export default function ClaimsPage() {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => { api.getClaims().then(setClaims).catch((cause: unknown) => setError(cause instanceof ClaimGuardApiError && cause.code === "API_CONFIGURATION_ERROR" ? cause.message : "We couldn't load claims right now. Please try again shortly.")).finally(() => setLoading(false)); }, []);
  if (loading) return <PageSkeleton />;
  return <div><div className="mb-8"><p className="text-sm font-semibold text-accent">Claim tracking</p><h1 className="mt-2 text-3xl font-semibold tracking-tight">Your claims</h1><p className="mt-2 text-[#66706A]">Keep an eye on every benefit you&apos;ve put to work.</p></div>{error ? <Notice message={error} /> : claims.length === 0 ? <EmptyClaims /> : <ClaimsTable claims={claims} />}</div>;
}

function ClaimsTable({ claims }: { claims: Claim[] }) { return <div className="overflow-hidden rounded-2xl border border-line bg-white shadow-card"><div className="hidden grid-cols-[1.4fr_1.6fr_.8fr_.8fr_1fr_24px] gap-4 border-b border-line px-6 py-4 text-xs font-semibold uppercase tracking-[.08em] text-[#778079] md:grid"><span>Benefit</span><span>Transaction</span><span>Amount</span><span>Status</span><span>Created</span><span /></div>{claims.map((claim) => <Link href={`/claims/${claim.id}`} key={claim.id} className="grid gap-3 border-b border-line px-6 py-5 transition last:border-0 hover:bg-[#FAFBF9] md:grid-cols-[1.4fr_1.6fr_.8fr_.8fr_1fr_24px] md:items-center md:gap-4"><div className="font-semibold">{formatBenefit(claim.benefit_type)}</div><div className="text-sm text-[#66706A]"><span className="md:hidden">Transaction: </span>{claim.transaction_id}</div><div className="font-medium tabular-nums">{formatMoney(claim.amount)}</div><div><span className="inline-flex rounded-full bg-accent-soft px-2.5 py-1 text-xs font-semibold text-accent">{claim.status}</span></div><div className="text-sm text-[#66706A]">{formatDate(claim.created_at)}</div><ArrowRight className="hidden text-[#8B938D] md:block" size={16} /></Link>)}</div>; }
function EmptyClaims() { return <div className="rounded-2xl border border-dashed border-[#C8CEC6] bg-white p-14 text-center"><div className="mx-auto grid size-12 place-items-center rounded-xl bg-accent-soft text-accent"><FileCheck2 size={22} /></div><h2 className="mt-4 font-semibold">No claims started yet.</h2><p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-[#66706A]">When a transaction qualifies, you can start and track its claim here.</p></div>; }
function Notice({ message }: { message: string }) { return <div className="rounded-2xl border border-line bg-white p-8 text-center text-[#66706A]">{message}</div>; }
