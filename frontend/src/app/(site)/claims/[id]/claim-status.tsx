"use client";

import { CheckIcon, CircleCheckIcon, ClockIcon, CopyIcon, InfoIcon, Loader2Icon } from "lucide-react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { ApiError, type Claim, getClaim } from "@/lib/api";
import { formatDate, formatRupees } from "@/lib/format";
import { cn } from "@/lib/utils";

const POLL_MS = 3000;
const SLOW_POLL_MS = 15000;
const FAST_POLLS = 40; // about 2 minutes of fast refresh, then every 15 seconds

const REASON_STYLE = {
  processing: "border-amber-400 bg-amber-50 text-amber-900",
  approved: "border-green-600 bg-green-50 text-green-900",
  rejected: "border-red-600 bg-red-50 text-red-900",
  officer_review: "border-blue-600 bg-blue-50 text-blue-900",
} as const;

export function ClaimStatusView() {
  const { id } = useParams<{ id: string }>();
  const isNew = useSearchParams().get("new") === "1";
  const claimId = decodeURIComponent(id).toUpperCase();

  const [claim, setClaim] = useState<Claim | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [copied, setCopied] = useState(false);

  // Load the claim, then keep refreshing while the AI is still working
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    let stopped = false;
    let polls = 0;

    async function load() {
      try {
        const data = await getClaim(claimId);
        if (stopped) return;
        setClaim(data);
        setError(null);
        polls += 1;
        if (data.status === "processing") timer = setTimeout(load, polls < FAST_POLLS ? POLL_MS : SLOW_POLL_MS);
      } catch (err) {
        if (stopped) return;
        setError(err instanceof ApiError ? err : new ApiError(0, "Something went wrong."));
        // Network blips: try again; "not found" is final
        if (!(err instanceof ApiError && err.status === 404)) timer = setTimeout(load, SLOW_POLL_MS);
      }
    }

    load();
    return () => { stopped = true; clearTimeout(timer); };
  }, [claimId]);

  async function copyId() {
    try {
      await navigator.clipboard.writeText(claimId);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // clipboard blocked (permissions/insecure page): the ID is still visible to copy by hand
    }
  }

  if (error?.status === 404) {
    return (
      <div className="mx-auto flex max-w-md flex-1 flex-col items-center justify-center gap-2 px-4 py-24 text-center">
        <h1 className="text-xl font-medium">Claim not found</h1>
        <p className="text-sm text-muted-foreground">We couldn&apos;t find {claimId}. Check the Claim ID and try again.</p>
        <Button asChild className="mt-3"><Link href="/track">Track a claim</Link></Button>
      </div>
    );
  }

  if (!claim) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 py-24 text-sm text-muted-foreground">
        <Spinner className="size-6 text-brand-600" />
        {error ? error.message : "Loading your claim…"}
      </div>
    );
  }

  const processing = claim.status === "processing";
  const decided = claim.status === "approved" || claim.status === "rejected";

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6">
      {isNew && (
        <div className="mb-6 flex items-start gap-3 rounded-xl border border-brand-100 bg-brand-50 p-4 text-sm text-brand-800">
          <CircleCheckIcon className="mt-0.5 size-5 shrink-0 text-brand-600" />
          <div>
            <p className="font-medium text-brand-900">Claim submitted</p>
            <p>Save your Claim ID to check the status later. This page updates by itself.</p>
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs text-muted-foreground">Claim ID</p>
          <h1 className="flex items-center gap-2 font-mono text-2xl font-medium text-brand-900">
            {claim.claim_id}
            <button onClick={copyId} aria-label="Copy Claim ID" className="text-brand-600 hover:text-brand-800">
              {copied ? <CheckIcon className="size-4" /> : <CopyIcon className="size-4" />}
            </button>
          </h1>
        </div>
        <StatusBadge status={claim.status} className="px-3 py-1 text-sm" />
      </div>

      {/* Progress steps */}
      <ol className="mt-6 flex items-center gap-2 text-xs">
        <Step done label="Submitted" />
        <Line done />
        <Step done={!processing} active={processing} label="AI review" />
        <Line done={!processing} />
        <Step
          done={decided}
          waiting={claim.status === "officer_review"}
          label={claim.status === "officer_review" ? "Waiting for officer" : "Decision"}
        />
      </ol>

      <div className={cn("mt-6 border-l-[3px] px-4 py-3 text-sm", REASON_STYLE[claim.status])}>
        <InfoIcon className="mr-1.5 inline size-4 align-[-3px]" />
        {processing
          ? "Our AI is reading your bill and checking your policy. This usually takes under a minute."
          : claim.message}
        {claim.officer_note && <p className="mt-1.5"><span className="font-medium">Officer note:</span> {claim.officer_note}</p>}
      </div>

      <dl className="mt-6 grid gap-x-6 gap-y-4 rounded-xl bg-cream p-5 text-sm sm:grid-cols-2">
        <Detail label="Patient" value={claim.patient_name} />
        <Detail label="Policy number" value={claim.policy_number} />
        <Detail label="Hospital" value={claim.hospital_name} />
        <Detail label="Treatment" value={claim.treatment} />
        <Detail label="Stay" value={`${formatDate(claim.admission_date)} – ${formatDate(claim.discharge_date)}`} />
        <Detail label="Amount" value={formatRupees(claim.amount)} highlight />
        {claim.description && <Detail label="Description" value={claim.description} />}
      </dl>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">
          {processing ? `Refreshing every ${POLL_MS / 1000} seconds…` : `Submitted ${formatDate(claim.created_at)}`}
        </p>
        <Button asChild variant="outline" className="border-brand-200 text-brand-800">
          <Link href="/track">Track another claim</Link>
        </Button>
      </div>
    </div>
  );
}

// done = finished (tick), active = AI working now (spinner), waiting = paused for a human (clock)
function Step({ label, done = false, active = false, waiting = false }: {
  label: string; done?: boolean; active?: boolean; waiting?: boolean;
}) {
  return (
    <li className={cn(
      "flex items-center gap-1.5",
      waiting ? "text-blue-800" : done || active ? "text-brand-600" : "text-muted-foreground",
    )}>
      <span className={cn(
        "flex size-6 items-center justify-center rounded-full",
        done ? "bg-brand-600 text-white"
          : waiting ? "bg-blue-50 text-blue-800 ring-2 ring-blue-200"
          : active ? "border-2 border-brand-400 text-brand-600"
          : "border-2 border-border",
      )}>
        {done ? <CheckIcon className="size-3.5" />
          : waiting ? <ClockIcon className="size-3.5" />
          : active ? <Loader2Icon className="size-3.5 animate-spin" />
          : null}
      </span>
      {label}
    </li>
  );
}

function Line({ done = false }: { done?: boolean }) {
  return <li aria-hidden className={cn("h-0.5 flex-1", done ? "bg-brand-200" : "bg-border")} />;
}

function Detail({ label, value, highlight = false }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div>
      <dt className="text-muted-foreground">{label}</dt>
      <dd className={cn("font-medium", highlight && "text-brand-600")}>{value}</dd>
    </div>
  );
}
