import Link from "next/link";

import { DemoBanner, SiteFooter, SiteHeader } from "@/components/site-header";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <>
      <DemoBanner />
      <SiteHeader />
      <main className="flex flex-1 flex-col items-center justify-center gap-3 px-4 py-24 text-center">
        <p className="text-sm font-medium text-brand-600">404</p>
        <h1 className="text-2xl font-medium">Page not found</h1>
        <p className="text-sm text-muted-foreground">The page you&apos;re looking for doesn&apos;t exist.</p>
        <Button asChild className="mt-2"><Link href="/">Back to home</Link></Button>
      </main>
      <SiteFooter />
    </>
  );
}
