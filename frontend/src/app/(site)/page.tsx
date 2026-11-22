import {
  ArrowRightIcon,
  BookOpenIcon,
  BotIcon,
  CircleCheckIcon,
  FilePlusIcon,
  FileTextIcon,
  SearchIcon,
  ShieldAlertIcon,
  SparklesIcon,
  UploadIcon,
  UserCheckIcon,
} from "lucide-react";
import Link from "next/link";

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const STEPS = [
  { icon: UploadIcon, title: "1. Submit", text: "Fill the form and upload your bill PDF", color: "bg-brand-50 text-brand-600" },
  { icon: BotIcon, title: "2. AI review", text: "Bill, policy, and fraud checks", color: "bg-violet-50 text-violet-700" },
  { icon: CircleCheckIcon, title: "3. Decision", text: "Approved, rejected, or sent to an officer", color: "bg-green-50 text-green-700" },
];

const FEATURES = [
  { icon: FileTextIcon, title: "Reads your bill", text: "Matches every detail with your form", color: "bg-blue-50 text-blue-700" },
  { icon: BookOpenIcon, title: "Checks your policy", text: "Shows the exact section used", color: "bg-brand-50 text-brand-600" },
  { icon: ShieldAlertIcon, title: "Spots fraud", text: "Flags anything unusual", color: "bg-orange-50 text-orange-800" },
  { icon: UserCheckIcon, title: "Human review", text: "Big or unclear claims go to an officer", color: "bg-amber-50 text-amber-800" },
];

const FAQ = [
  { q: "What file types can I upload?", a: "A text-based PDF of your hospital bill, up to 5 MB and 10 pages." },
  { q: "How long does a review take?", a: "Usually under a minute. Your claim page updates by itself while the AI works." },
  { q: "Does a human ever check my claim?", a: "Yes. Claims above Rs 50,000, unclear cases, and anything that looks unusual go to a claims officer." },
];

export default function LandingPage() {
  return (
    <>
      {/* Hero */}
      <section className="bg-brand-50">
        <div className="mx-auto grid max-w-6xl items-center gap-10 px-4 py-14 sm:px-6 md:grid-cols-[1.3fr_1fr] md:py-20">
          <div>
            <Badge variant="outline" className="rounded-full border-brand-100 bg-white text-brand-600">
              <SparklesIcon /> AI-powered health claims
            </Badge>
            <h1 className="mt-4 text-3xl font-medium leading-tight text-brand-900 sm:text-4xl">
              Health claims reviewed in <span className="text-brand-600">minutes</span>, not weeks
            </h1>
            <p className="mt-3 max-w-md text-brand-800">
              Upload your hospital bill. Our AI reads it, checks your policy, and gives you a clear answer.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link href="/claims/new"><FilePlusIcon /> Submit a claim</Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="border-brand-200 bg-white text-brand-800">
                <Link href="/track"><SearchIcon /> Track a claim</Link>
              </Button>
            </div>
          </div>

          {/* Example result card */}
          <div className="rounded-2xl border border-brand-100 bg-white p-5">
            <div className="flex items-center justify-between">
              <span className="font-mono text-sm font-medium">CLM-7F3K-Q9XA</span>
              <Badge variant="outline" className="rounded-full border-green-200 bg-green-50 text-green-900">
                <CircleCheckIcon /> Approved
              </Badge>
            </div>
            <ul className="mt-3 space-y-1.5 text-sm text-muted-foreground">
              {["Bill read and matched", "Policy Section 2.1: covered", "Fraud risk: low"].map((line) => (
                <li key={line} className="flex items-center gap-2">
                  <CircleCheckIcon className="size-4 text-brand-400" /> {line}
                </li>
              ))}
            </ul>
            <p className="mt-4 rounded-lg bg-brand-50 px-3 py-2 text-sm text-brand-800">Rs 18,500 approved in 12 seconds</p>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="mx-auto w-full max-w-6xl scroll-mt-16 px-4 py-16 sm:px-6">
        <p className="text-center text-xs font-medium tracking-wide text-brand-600">HOW IT WORKS</p>
        <h2 className="mt-1 text-center text-2xl font-medium">Three simple steps</h2>
        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {STEPS.map(({ icon: Icon, title, text, color }) => (
            <div key={title} className="rounded-xl border bg-white p-6 text-center">
              <span className={`inline-flex size-11 items-center justify-center rounded-xl ${color}`}><Icon className="size-5" /></span>
              <h3 className="mt-3 font-medium">{title}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="bg-cream">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
          <p className="text-center text-xs font-medium tracking-wide text-brand-600">FEATURES</p>
          <h2 className="mt-1 text-center text-2xl font-medium">What our AI checks</h2>
          <div className="mt-8 grid gap-4 sm:grid-cols-2">
            {FEATURES.map(({ icon: Icon, title, text, color }) => (
              <div key={title} className="flex gap-4 rounded-xl border bg-white p-5">
                <span className={`flex size-11 shrink-0 items-center justify-center rounded-xl ${color}`}><Icon className="size-5" /></span>
                <div>
                  <h3 className="font-medium">{title}</h3>
                  <p className="mt-0.5 text-sm text-muted-foreground">{text}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="mx-auto w-full max-w-2xl px-4 py-16 sm:px-6">
        <h2 className="text-center text-2xl font-medium">Questions</h2>
        <Accordion type="single" collapsible className="mt-6">
          {FAQ.map(({ q, a }) => (
            <AccordionItem key={q} value={q}>
              <AccordionTrigger className="text-base">{q}</AccordionTrigger>
              <AccordionContent className="text-muted-foreground">{a}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </section>

      {/* Call to action */}
      <section className="mx-auto w-full max-w-6xl px-4 pb-16 sm:px-6">
        <div className="flex flex-col items-start justify-between gap-4 rounded-2xl bg-brand-600 p-7 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-xl font-medium text-white">Ready to submit your claim?</h2>
            <p className="mt-1 text-sm text-brand-100">It takes about 2 minutes.</p>
          </div>
          <Button asChild size="lg" variant="outline" className="border-0 bg-white text-brand-800 hover:bg-brand-50">
            <Link href="/claims/new">Submit a claim <ArrowRightIcon /></Link>
          </Button>
        </div>
      </section>
    </>
  );
}
