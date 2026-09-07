"use client";

import { ArrowRight, CheckCircle2, CircleDollarSign, FilePlus2, Search, Sparkles } from "lucide-react";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { formatBenefit, formatDate, formatMoney, sumMoney } from "@/lib/format";
import type { Claim, EligibilityResponse, Transaction } from "@/lib/types";
import { PageSkeleton } from "@/components/ui";

type TransactionCoverage = {
  transaction: Transaction;
  eligibility: EligibilityResponse;
};

export default function DashboardPage() {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [transactions, setTransactions] = useState<TransactionCoverage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [transactionId, setTransactionId] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [transactionRecords, claimRecords] = await Promise.all([
          api.getTransactions(),
          api.getClaims(),
        ]);
        const coverage = await Promise.all(
          transactionRecords.map(async (transaction) => ({
            transaction,
            eligibility: await api.getEligibility(transaction.id),
          })),
        );

        setTransactions(coverage);
        setClaims(claimRecords);
      } catch {
        setError("We couldn't load your dashboard right now. Please try again shortly.");
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  function findTransaction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (transactionId.trim()) {
      window.location.href = `/transactions/${encodeURIComponent(transactionId.trim())}`;
    }
  }

  if (loading) return <PageSkeleton />;

  const eligibleTransactions = transactions.filter(({ eligibility }) => eligibility.eligible);
  const potentialRecovery = sumMoney(
    eligibleTransactions.map(({ eligibility }) => eligibility.eligibleAmount),
  );
  const dashboardUnavailable = Boolean(error);

  return (
    <div className="space-y-9">
      <section className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
        <div>
          <p className="mb-2 flex items-center gap-2 text-sm font-semibold text-accent"><Sparkles size={16} /> Coverage, made visible</p>
          <h1 className="text-3xl font-semibold tracking-tight text-ink sm:text-4xl">You may already be covered.</h1>
          <p className="mt-2 max-w-xl text-[#66706A]">ClaimGuard helps turn card benefits into claims you can actually use.</p>
        </div>
        <Link href="/claims" className="inline-flex items-center gap-2 text-sm font-semibold text-accent hover:text-[#0A6045]">View all claims <ArrowRight size={16} /></Link>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Potential recovery" value={dashboardUnavailable ? "—" : formatMoney(potentialRecovery)} detail={dashboardUnavailable ? "Dashboard unavailable" : "Across eligible transactions"} emphasis icon={<CircleDollarSign size={20} />} />
        <StatCard label="Eligible transactions" value={dashboardUnavailable ? "—" : String(eligibleTransactions.length)} detail={dashboardUnavailable ? "Dashboard unavailable" : `${transactions.length} transactions reviewed`} />
        <StatCard label="Claims started" value={dashboardUnavailable ? "—" : String(claims.length)} detail={dashboardUnavailable ? "Dashboard unavailable" : claims.length === 1 ? "Claim in progress" : "Claims in progress"} icon={<FilePlus2 size={20} />} />
      </section>

      {error && <p className="rounded-xl bg-[#FFF6E9] px-4 py-3 text-sm text-[#76521F]">{error}</p>}

      <section className="rounded-2xl border border-line bg-white p-6 shadow-card sm:p-7">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div><h2 className="text-xl font-semibold">Review a transaction</h2><p className="mt-1 text-sm text-[#66706A]">Enter a transaction ID to check the coverage decision from ClaimGuard.</p></div>
          <form onSubmit={findTransaction} className="flex w-full gap-2 sm:w-auto"><input value={transactionId} onChange={(event) => setTransactionId(event.target.value)} placeholder="Transaction ID" className="min-w-0 flex-1 rounded-xl border border-line bg-canvas px-4 py-2.5 text-sm outline-none transition focus:border-accent focus:ring-4 focus:ring-accent/10 sm:w-64" /><button className="inline-flex shrink-0 items-center gap-2 rounded-xl bg-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#0A6045] active:scale-[.98]"><Search size={16} /> Check</button></form>
        </div>
      </section>

      <section>
        <div className="mb-4"><h2 className="text-xl font-semibold">Transactions</h2><p className="mt-1 text-sm text-[#66706A]">Your recent card activity and available coverage.</p></div>
        {error ? <DashboardError /> : transactions.length === 0 ? <EmptyTransactions /> : <TransactionsTable transactions={transactions} />}
      </section>
    </div>
  );
}

function TransactionsTable({ transactions }: { transactions: TransactionCoverage[] }) {
  return <div className="overflow-hidden rounded-2xl border border-line bg-white shadow-card"><div className="hidden grid-cols-[1.3fr_.8fr_1.3fr_.8fr_1fr_24px] gap-4 border-b border-line px-6 py-4 text-xs font-semibold uppercase tracking-[.08em] text-[#778079] lg:grid"><span>Merchant</span><span>Amount</span><span>Coverage</span><span>Potential</span><span>Date</span><span /></div>{transactions.map(({ transaction, eligibility }) => <Link href={`/transactions/${transaction.id}`} key={transaction.id} className="grid gap-3 border-b border-line px-6 py-5 transition last:border-0 hover:bg-[#FAFBF9] lg:grid-cols-[1.3fr_.8fr_1.3fr_.8fr_1fr_24px] lg:items-center lg:gap-4"><div><p className="font-semibold">{transaction.merchant}</p><p className="mt-1 text-xs text-[#778079]">{transaction.currency}</p></div><div className="font-medium tabular-nums">{formatMoney(transaction.amount, transaction.currency)}</div><div>{eligibility.eligible ? <span className="inline-flex items-center gap-1.5 rounded-full bg-accent-soft px-2.5 py-1 text-xs font-semibold text-accent"><CheckCircle2 size={13} /> {formatBenefit(eligibility.benefitType ?? "")}</span> : <span className="inline-flex rounded-full bg-[#EEF0ED] px-2.5 py-1 text-xs font-semibold text-[#657068]">Not eligible</span>}</div><div className="font-medium tabular-nums text-accent">{eligibility.eligible ? formatMoney(eligibility.eligibleAmount) : "—"}</div><div className="text-sm text-[#66706A]">{formatDate(transaction.transaction_date)}</div><ArrowRight className="hidden text-[#8B938D] lg:block" size={16} /></Link>)}</div>;
}

function EmptyTransactions() { return <div className="rounded-2xl border border-dashed border-[#C8CEC6] bg-white p-14 text-center"><div className="mx-auto mb-3 grid size-11 place-items-center rounded-xl bg-accent-soft text-accent"><Search size={20} /></div><h3 className="font-semibold">No transactions to review.</h3><p className="mx-auto mt-2 max-w-md text-sm leading-6 text-[#66706A]">New card transactions will appear here when ClaimGuard receives them.</p></div>; }
function DashboardError() { return <div className="rounded-2xl border border-line bg-white p-10 text-center shadow-card"><h3 className="font-semibold">Your transaction feed is unavailable.</h3><p className="mt-2 text-sm text-[#66706A]">Please refresh the page or try again shortly.</p></div>; }
function StatCard({ label, value, detail, emphasis, icon }: { label: string; value: string; detail: string; emphasis?: boolean; icon?: React.ReactNode }) { return <article className={`rounded-2xl border p-6 shadow-card ${emphasis ? "border-[#BFE4D1] bg-accent-soft" : "border-line bg-white"}`}><div className="flex items-center justify-between text-sm font-medium text-[#66706A]"><span>{label}</span>{icon && <span className="text-accent">{icon}</span>}</div><p className={`mt-5 font-semibold tabular-nums tracking-tight ${emphasis ? "text-5xl text-accent" : "text-4xl text-ink"}`}>{value}</p><p className="mt-2 text-sm text-[#66706A]">{detail}</p></article>; }
