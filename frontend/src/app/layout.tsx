import type { Metadata } from "next";
import "./globals.css";
import { Navigation } from "@/components/navigation";

export const metadata: Metadata = { title: "ClaimGuard", description: "Find card benefits you may already have." };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><Navigation /><main className="mx-auto min-h-[calc(100vh-73px)] max-w-6xl px-5 py-9 lg:px-8 lg:py-12">{children}</main></body></html>;
}
