"use client";

import { CheckCircle2, CircleAlert, Copy } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, ClaimGuardApiError } from "@/lib/api";
import { formatBenefit, formatDate, formatMoney } from "@/lib/format";
import type { Claim } from "@/lib/types";
import { PageSkeleton } from "@/components/ui";

export default function ClaimDetailsPage() {
  const { claimId } = useParams<{ claimId: string }>();
  const [claim, setClaim] = useState<Claim | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { api.getClaim(claimId).then(setClaim).catch((cause: unknown) => setError(cause instanceof ClaimGuardApiError && cause.code === "CLAIM_NOT_FOUND" ? "This claim could not be found." : "We couldn't load this claim right now.")).finally(() => undefined); }, [claimId]);
  if (error) return <div className="rounded-2xl border border-line bg-white p-10 text-center shadow-card"><CircleAlert className="mx-auto text-[#8B938D]" /><h1 className="mt-4 text-xl font-semibold">Claim unavailable</h1><p className="mt-2 text-sm text-[#66706A]">{error}</p></div>;
  if (!claim) return <PageSkeleton />;
  const fields = [["Claim ID", claim.id], ["Transaction ID", claim.transaction_id], ["Benefit type", formatBenefit(claim.benefit_type)], ["Claim amount", formatMoney(claim.amount)], ["Created", formatDate(claim.created_at)]];
  return <div className="mx-auto max-w-3xl"><Link href="/claims" className="text-sm font-semibold text-accent">← Back to claims</Link><section className="mt-6 overflow-hidden rounded-2xl border border-line bg-white shadow-card"><div className="flex items-start justify-between bg-accent-soft p-7"><div><p className="flex items-center gap-2 text-sm font-semibold text-accent"><CheckCircle2 size={18} /> Claim tracking</p><h1 className="mt-3 text-2xl font-semibold tracking-tight">{formatBenefit(claim.benefit_type)}</h1></div><span className="rounded-full bg-white px-3 py-1.5 text-sm font-semibold text-accent shadow-sm">{claim.status}</span></div><dl className="divide-y divide-line p-7">{fields.map(([label, value]) => <div key={label} className="flex flex-col gap-1 py-4 first:pt-0 sm:flex-row sm:justify-between sm:gap-8"><dt className="text-sm text-[#66706A]">{label}</dt><dd className="flex items-center gap-2 break-all text-sm font-medium text-ink"><span>{value}</span>{label.endsWith("ID") && <Copy size={14} className="shrink-0 text-[#8B938D]" />}</dd></div>)}</dl></section></div>;
}
