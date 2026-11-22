"use client";

import { ChevronRightIcon, HashIcon, SearchIcon, UserIcon } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { PageHero } from "@/components/site-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { ApiError, type Claim, searchByPolicy } from "@/lib/api";
import { formatDate, formatRupees, isClaimId } from "@/lib/format";

export default function TrackPage() {
  const router = useRouter();

  // Option 1: Claim ID (the "receipt number" shown after submit)
  const [claimId, setClaimId] = useState("");
  const [idError, setIdError] = useState("");

  // Option 2: policy number + patient name (both must match)
  const [policy, setPolicy] = useState("");
  const [name, setName] = useState("");
  const [claims, setClaims] = useState<Claim[] | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function openClaim(event: React.FormEvent) {
    event.preventDefault();
    const id = claimId.trim().toUpperCase();
    if (!isClaimId(id)) {
      setIdError("Enter a Claim ID like CLM-7F3K-Q9XA.");
      return;
    }
    router.push(`/claims/${encodeURIComponent(id)}`);
  }

  async function findClaims(event: React.FormEvent) {
    event.preventDefault();
    if (policy.trim().length < 3 || name.trim().length < 2) {
      setError("Enter both the policy number and the patient name.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      setClaims(await searchByPolicy(policy.trim(), name.trim()));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
      setClaims(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHero title="Track your claim" subtitle="Use your Claim ID, or your policy number with the patient's name." />
      <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6">
        <div className="grid gap-4 md:grid-cols-2">
          {/* Option 1 */}
          <form onSubmit={openClaim} className="rounded-xl border bg-white p-5" noValidate>
            <h2 className="flex items-center gap-1.5 text-sm font-medium text-brand-600"><HashIcon className="size-4" /> I have my Claim ID</h2>
            <div className="mt-3 grid gap-1.5">
              <Label htmlFor="claim_id">Claim ID</Label>
              <Input
                id="claim_id"
                value={claimId}
                onChange={(e) => { setClaimId(e.target.value); setIdError(""); }}
                placeholder="CLM-7F3K-Q9XA"
                className="font-mono uppercase"
                aria-invalid={Boolean(idError)}
              />
              {idError && <p className="text-xs text-destructive">{idError}</p>}
            </div>
            <Button type="submit" className="mt-4 w-full"><SearchIcon /> Open claim</Button>
          </form>

          {/* Option 2 */}
          <form onSubmit={findClaims} className="rounded-xl border bg-white p-5" noValidate>
            <h2 className="flex items-center gap-1.5 text-sm font-medium text-brand-600"><UserIcon className="size-4" /> I lost my Claim ID</h2>
            <div className="mt-3 grid gap-3">
              <div className="grid gap-1.5">
                <Label htmlFor="policy">Policy number</Label>
                <Input id="policy" value={policy} onChange={(e) => { setPolicy(e.target.value); setError(""); }} placeholder="HLT-2026-0042" />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="patient">Patient name</Label>
                <Input id="patient" value={name} onChange={(e) => { setName(e.target.value); setError(""); }} placeholder="Ravi Kumar" autoComplete="name" />
              </div>
            </div>
            {error && <p className="mt-2 text-xs text-destructive">{error}</p>}
            <Button type="submit" variant="outline" className="mt-4 w-full border-brand-200 text-brand-800" disabled={loading}>
              {loading ? <Spinner /> : <SearchIcon />} Find my claims
            </Button>
          </form>
        </div>

        <div className="pt-8">
          {claims !== null && claims.length === 0 && (
            <div className="rounded-xl border border-dashed p-8 text-center">
              <p className="font-medium">No claims found</p>
              <p className="mt-1 text-sm text-muted-foreground">Check that the policy number and name match your claim form.</p>
            </div>
          )}

          {claims !== null && claims.length > 0 && (
            <>
              <p className="mb-3 text-sm text-muted-foreground">
                {claims.length} {claims.length === 1 ? "claim" : "claims"} found
              </p>
              <ul className="divide-y overflow-hidden rounded-xl border bg-white">
                {claims.map((claim) => (
                  <li key={claim.claim_id}>
                    <Link
                      href={`/claims/${claim.claim_id}`}
                      className="flex items-center justify-between gap-3 px-4 py-3.5 text-sm hover:bg-muted"
                    >
                      <span>
                        <span className="font-mono font-medium">{claim.claim_id}</span>
                        <span className="text-muted-foreground"> · {claim.treatment} · {formatRupees(claim.amount)} · {formatDate(claim.created_at)}</span>
                      </span>
                      <span className="flex items-center gap-2">
                        <StatusBadge status={claim.status} />
                        <ChevronRightIcon className="size-4 text-brand-600" />
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </div>
    </>
  );
}
