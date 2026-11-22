import { InfoIcon, LockIcon, ShieldCheckIcon } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";

export function Logo({ light = false }: { light?: boolean }) {
  return (
    <Link href="/" className={`flex items-center gap-2 font-medium ${light ? "text-white" : "text-brand-800"}`}>
      <span className={`flex size-7 items-center justify-center rounded-lg text-white ${light ? "bg-brand-400" : "bg-brand-600"}`}>
        <ShieldCheckIcon className="size-4" />
      </span>
      ClaimCare AI
    </Link>
  );
}

export function DemoBanner() {
  // Honest notice: this is a portfolio demo, so people should not upload real medical bills
  return (
    <div className="bg-amber-50 text-amber-900">
      <p className="mx-auto flex max-w-6xl items-center justify-center gap-1.5 px-4 py-1.5 text-center text-xs">
        <InfoIcon className="size-3.5 shrink-0" />
        Demo project: please don&apos;t upload real medical bills or personal details.
      </p>
    </div>
  );
}

export function SiteHeader() {
  return (
    <header className="border-b border-brand-50 bg-white">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Logo />
        <nav className="flex items-center gap-1 text-sm text-muted-foreground sm:gap-4">
          <Link href="/#how-it-works" className="hidden hover:text-foreground sm:block">How it works</Link>
          <Link href="/track" className="px-2 hover:text-foreground">Track claim</Link>
          <Button asChild variant="outline" size="sm" className="border-brand-200 text-brand-800">
            <Link href="/officer/login">
              <LockIcon /> <span className="hidden sm:inline">Officer login</span>
            </Link>
          </Button>
        </nav>
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="mt-auto bg-brand-900 text-xs text-brand-100">
      <div className="mx-auto flex max-w-6xl flex-col gap-1 px-4 py-4 sm:flex-row sm:justify-between sm:px-6">
        <span>ClaimCare AI · Demo project</span>
        <span>Built with Next.js, FastAPI, LangGraph</span>
      </div>
    </footer>
  );
}

export function PageHero({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <section className="bg-brand-50">
      <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
        <h1 className="text-2xl font-medium text-brand-900">{title}</h1>
        <p className="mt-1 text-sm text-brand-800">{subtitle}</p>
      </div>
    </section>
  );
}
