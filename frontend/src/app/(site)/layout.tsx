import { DemoBanner, SiteFooter, SiteHeader } from "@/components/site-header";

// Shared frame for all customer pages: white header + dark teal footer
export default function SiteLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <DemoBanner />
      <SiteHeader />
      <main className="flex flex-1 flex-col">{children}</main>
      <SiteFooter />
    </>
  );
}
