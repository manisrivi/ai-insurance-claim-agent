"use client";

import { CheckIcon, EyeIcon, InboxIcon, LogOutIcon, RefreshCwIcon, XIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ClaimDetailsDialog } from "@/components/claim-details-dialog";
import { Logo } from "@/components/site-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ApiError, decideClaim, getOfficerClaims, type OfficerClaim } from "@/lib/api";
import { formatRupees } from "@/lib/format";
import { clearOfficerKey, getOfficerKey } from "@/lib/officer-key";

// Short label for the AI reason column
function reasonTag(claim: OfficerClaim) {
  const reason = claim.reason ?? "";
  if (/could not be read/i.test(reason)) return { text: "Unreadable bill", className: "border-amber-200 bg-amber-50 text-amber-900" };
  if (/mismatch/i.test(reason)) return { text: "Mismatch", className: "border-red-200 bg-red-50 text-red-900" };
  if (/unclear|citation/i.test(reason)) return { text: "Coverage unclear", className: "border-amber-200 bg-amber-50 text-amber-900" };
  if (/failed/i.test(reason)) return { text: "AI failed", className: "border-amber-200 bg-amber-50 text-amber-900" };
  if (/limit|above/i.test(reason)) return { text: "Above limit", className: "border-blue-200 bg-blue-50 text-blue-900" };
  return { text: "Needs review", className: "border-blue-200 bg-blue-50 text-blue-900" };
}

export default function OfficerPage() {
  const router = useRouter();
  const [claims, setClaims] = useState<OfficerClaim[] | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<OfficerClaim | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  // Row buttons need two clicks: first click asks "Confirm?", second click decides
  const [confirming, setConfirming] = useState<{ id: string; decision: "approved" | "rejected" } | null>(null);

  const logout = useCallback(() => {
    clearOfficerKey();
    router.replace("/officer/login");
  }, [router]);

  // Fetch the list; state is only updated after the request finishes
  const fetchClaims = useCallback((key: string) => {
    return getOfficerClaims(key)
      .then((data) => {
        setClaims(data);
        setError("");
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) return logout();
        setError(err instanceof ApiError ? err.message : "Couldn't load claims.");
      })
      .finally(() => setLoading(false));
  }, [logout]);

  function load(key: string) {
    setLoading(true);
    fetchClaims(key);
  }

  // No key in this tab? Go to the login page
  useEffect(() => {
    const key = getOfficerKey();
    if (!key) {
      router.replace("/officer/login");
      return;
    }
    fetchClaims(key);
  }, [router, fetchClaims]);

  async function decide(claimId: string, decision: "approved" | "rejected", note = "") {
    const officerKey = getOfficerKey();
    if (!officerKey) return logout();
    setBusyId(claimId);
    try {
      await decideClaim(officerKey, claimId, decision, note);
      setClaims((prev) => prev?.filter((c) => c.claim_id !== claimId) ?? null);
      setSelected(null);
      setMessage(`${claimId} ${decision}`);
      setTimeout(() => setMessage(""), 3000);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't save the decision.");
    } finally {
      setBusyId(null);
    }
  }

  function rowClick(claimId: string, decision: "approved" | "rejected") {
    if (confirming?.id === claimId && confirming.decision === decision) {
      setConfirming(null);
      decide(claimId, decision);
      return;
    }
    setConfirming({ id: claimId, decision });
    setTimeout(() => setConfirming((c) => (c?.id === claimId && c.decision === decision ? null : c)), 4000);
  }

  const highRisk = claims?.filter((c) => c.risk === "high").length ?? 0;
  const total = claims?.reduce((sum, c) => sum + c.amount, 0) ?? 0;

  return (
    <>
      <header className="bg-brand-900">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-2">
            <Logo light />
            <Badge className="rounded-full bg-brand-800 font-normal text-brand-100">Officer</Badge>
          </div>
          <Button variant="outline" size="sm" onClick={logout} className="border-brand-600 bg-transparent text-brand-100 hover:bg-brand-800 hover:text-white">
            <LogOutIcon /> Log out
          </Button>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">
        {/* Summary cards */}
        <div className="grid gap-3 sm:grid-cols-3">
          <Stat label="Waiting for review" value={claims?.length ?? "-"} className="bg-blue-50 text-blue-900" />
          <Stat label="High risk" value={claims ? highRisk : "-"} className="bg-red-50 text-red-900" />
          <Stat label="Total amount" value={claims ? formatRupees(total) : "-"} className="bg-brand-50 text-brand-900" />
        </div>

        <div className="mb-3 mt-8 flex items-center justify-between">
          <h1 className="text-lg font-medium">Claims waiting for review</h1>
          <Button variant="outline" size="sm" disabled={loading} onClick={() => { const key = getOfficerKey(); if (key) load(key); else logout(); }} className="border-brand-200 text-brand-800">
            {loading ? <Spinner /> : <RefreshCwIcon />} Refresh
          </Button>
        </div>

        {message && <p className="mb-3 rounded-lg border border-brand-100 bg-brand-50 px-3 py-2 text-sm text-brand-800">{message}</p>}
        {error && <p className="mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">{error}</p>}

        {claims === null ? (
          <div className="flex justify-center py-16"><Spinner className="size-6 text-brand-600" /></div>
        ) : claims.length === 0 ? (
          <div className="flex flex-col items-center rounded-xl border border-dashed py-14 text-center">
            <InboxIcon className="size-8 text-brand-400" />
            <p className="mt-2 font-medium">All caught up</p>
            <p className="text-sm text-muted-foreground">No claims are waiting for review.</p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl border bg-white">
            <Table>
              <TableHeader className="bg-cream">
                <TableRow>
                  <TableHead>Claim ID</TableHead>
                  <TableHead>Patient</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>AI reason</TableHead>
                  <TableHead className="text-center">View</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {claims.map((claim) => {
                  const tag = reasonTag(claim);
                  const busy = busyId === claim.claim_id;
                  return (
                    <TableRow key={claim.claim_id}>
                      <TableCell className="font-mono">{claim.claim_id}</TableCell>
                      <TableCell>{claim.patient_name}</TableCell>
                      <TableCell>{formatRupees(claim.amount)}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={`rounded-full ${tag.className}`} title={claim.reason ?? ""}>{tag.text}</Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        <Button variant="ghost" size="icon" aria-label={`View ${claim.claim_id}`} onClick={() => setSelected(claim)} className="text-brand-600 hover:bg-brand-50 hover:text-brand-800">
                          <EyeIcon />
                        </Button>
                      </TableCell>
                      <TableCell>
                        <div className="flex justify-end gap-1.5">
                          <Button
                            size="sm"
                            disabled={busy}
                            onClick={() => rowClick(claim.claim_id, "approved")}
                            className={confirming?.id === claim.claim_id && confirming.decision === "approved"
                              ? "bg-green-700 text-white hover:bg-green-800"
                              : "bg-green-50 text-green-900 hover:bg-green-100"}
                          >
                            {busy ? <Spinner /> : <CheckIcon />}
                            {confirming?.id === claim.claim_id && confirming.decision === "approved" ? "Confirm?" : "Approve"}
                          </Button>
                          <Button
                            size="sm"
                            disabled={busy}
                            onClick={() => rowClick(claim.claim_id, "rejected")}
                            className={confirming?.id === claim.claim_id && confirming.decision === "rejected"
                              ? "bg-red-700 text-white hover:bg-red-800"
                              : "bg-red-50 text-red-900 hover:bg-red-100"}
                          >
                            <XIcon />
                            {confirming?.id === claim.claim_id && confirming.decision === "rejected" ? "Confirm?" : "Reject"}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </main>

      <ClaimDetailsDialog claim={selected} onClose={() => setSelected(null)} onDecide={decide} />
    </>
  );
}

function Stat({ label, value, className }: { label: string; value: string | number; className: string }) {
  return (
    <div className={`rounded-xl px-4 py-3 ${className}`}>
      <p className="text-xs opacity-80">{label}</p>
      <p className="mt-0.5 text-2xl font-medium">{value}</p>
    </div>
  );
}
