"use client";

import { LayoutDashboard, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/claims", label: "Claims", icon: ShieldCheck },
];

export function Navigation() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-20 border-b border-line/80 bg-canvas/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 lg:px-8">
        <Link href="/" className="flex items-center gap-2 text-lg font-semibold tracking-tight text-ink">
          <span className="grid size-8 place-items-center rounded-lg bg-accent text-white"><ShieldCheck size={18} /></span>
          ClaimGuard
        </Link>
        <nav className="flex items-center gap-1 rounded-xl bg-[#ECEFE9] p-1" aria-label="Main navigation">
          {links.map(({ href, label, icon: Icon }) => {
            const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link key={href} href={href} className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${active ? "bg-white text-ink shadow-sm" : "text-[#66706A] hover:text-ink"}`}>
                <Icon size={16} /> <span className="hidden sm:inline">{label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
