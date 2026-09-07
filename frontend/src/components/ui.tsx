import { LoaderCircle } from "lucide-react";

export function PageSkeleton() {
  return <div className="animate-pulse space-y-6"><div className="h-9 w-48 rounded bg-[#E9ECE6]" /><div className="grid gap-4 md:grid-cols-3">{[1, 2, 3].map((item) => <div key={item} className="h-36 rounded-2xl bg-[#E9ECE6]" />)}</div><div className="h-72 rounded-2xl bg-[#E9ECE6]" /></div>;
}

export function LoadingButton({ children }: { children: string }) {
  return <span className="inline-flex items-center gap-2"><LoaderCircle size={16} className="animate-spin" />{children}</span>;
}
