"use client";

import { AlertTriangleIcon, BotIcon, CheckIcon, XIcon } from "lucide-react";
import { useState } from "react";

import { RiskBadge, StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import type { OfficerClaim } from "@/lib/api";
import { formatDate, formatDateTime, formatRupees } from "@/lib/format";
import { cn } from "@/lib/utils";

type Decision = "approved" | "rejected";

type Props = {
  claim: OfficerClaim | null;
  onClose: () => void;
  onDecide: (claimId: string, decision: Decision, note: string) => Promise<void>;
};

// Same rule as the backend: ignore case, spaces and punctuation ("Mayo Clinic" = "mayoclinic")
const normalize = (text: string) => text.toLowerCase().replace(/[^a-z0-9]/g, "");

function sameText(a?: string | null, b?: string | null) {
  if (!a || !b) return true;
  const x = normalize(a);
  const y = normalize(b);
  return x.includes(y) || y.includes(x);
}

export function ClaimDetailsDialog({ claim, onClose, onDecide }: Props) {
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState<Decision | null>(null);

  async function decide(decision: Decision) {
    if (!claim) return;
    setBusy(decision);
    try {
      await onDecide(claim.claim_id, decision, note);
      setNote("");
    } finally {
      setBusy(null);
    }
  }

  const bill = claim?.extracted_details ?? {};
  const billAmount = bill.total_amount ?? null;
  const amountMismatch = claim && billAmount !== null && Math.abs(claim.amount - billAmount) > billAmount * 0.01;

  return (
    <Dialog open={claim !== null} onOpenChange={(open) => { if (!open) { setNote(""); onClose(); } }}>
      <DialogContent className="gap-0 overflow-hidden p-0 sm:max-w-2xl">
        {claim && (
          <>
            <DialogHeader className="flex-row items-start justify-between gap-3 bg-brand-50 px-6 py-4 pr-12 text-left">
              <div>
                <DialogTitle className="font-mono text-lg text-brand-900">{claim.claim_id}</DialogTitle>
                <DialogDescription className="text-brand-800">Submitted {formatDateTime(claim.created_at)}</DialogDescription>
              </div>
              <div className="flex flex-wrap justify-end gap-1.5">
                <StatusBadge status={claim.status} />
                <RiskBadge risk={claim.risk} />
              </div>
            </DialogHeader>

            <div className="max-h-[70vh] overflow-y-auto px-6 py-5">
              <h3 className="mb-2 text-sm font-medium text-brand-600">Customer details vs bill (read by AI)</h3>
              <div className="overflow-hidden rounded-lg border text-sm">
                <div className="grid grid-cols-[1fr_1.3fr_1.3fr] gap-2 bg-cream px-3 py-2 text-xs text-muted-foreground">
                  <span>Field</span><span>Form says</span><span>Bill says</span>
                </div>
                <Row label="Patient" form={claim.patient_name} bill={bill.patient_name} ok={sameText(claim.patient_name, bill.patient_name)} />
                <Row label="Policy no." form={claim.policy_number} bill={null} ok />
                <Row label="Hospital" form={claim.hospital_name} bill={bill.hospital_name} ok={sameText(claim.hospital_name, bill.hospital_name)} />
                <Row label="Treatment" form={claim.treatment} bill={bill.treatment} ok />
                <Row
                  label="Admission"
                  form={formatDate(claim.admission_date)}
                  bill={bill.admission_date ? formatDate(bill.admission_date) : null}
                  ok={!bill.admission_date || bill.admission_date === claim.admission_date}
                />
                <Row
                  label="Discharge"
                  form={formatDate(claim.discharge_date)}
                  bill={bill.discharge_date ? formatDate(bill.discharge_date) : null}
                  ok={!bill.discharge_date || bill.discharge_date === claim.discharge_date}
                />
                <Row label="Amount" form={formatRupees(claim.amount)} bill={billAmount !== null ? formatRupees(billAmount) : null} ok={!amountMismatch} />
                <div className="grid grid-cols-[1fr_2.6fr] gap-2 border-t px-3 py-2">
                  <span className="text-muted-foreground">Description</span>
                  <span>{claim.description || "-"}</span>
                </div>
              </div>

              <h3 className="mb-2 mt-5 text-sm font-medium text-brand-600">AI review</h3>
              <p className="flex gap-2 rounded-lg bg-violet-50 px-3 py-2.5 text-sm text-violet-900">
                <BotIcon className="mt-0.5 size-4 shrink-0" /> {claim.reason || "No AI notes."}
              </p>

              <div className="mt-5 grid gap-1.5">
                <Label htmlFor="note">Officer note</Label>
                <Textarea
                  id="note"
                  rows={2}
                  maxLength={1000}
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Called the hospital. Bill amount is Rs 6,500."
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 border-t px-6 py-4">
              <Button variant="outline" onClick={onClose} className="border-brand-200 text-brand-800">Close</Button>
              <Button
                variant="outline"
                disabled={busy !== null}
                onClick={() => decide("rejected")}
                className="border-red-300 text-red-800 hover:bg-red-50 hover:text-red-900"
              >
                {busy === "rejected" ? <Spinner /> : <XIcon />} Reject
              </Button>
              <Button disabled={busy !== null} onClick={() => decide("approved")}>
                {busy === "approved" ? <Spinner /> : <CheckIcon />} Approve
              </Button>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}

function Row({ label, form, bill, ok }: { label: string; form: string; bill: string | null | undefined; ok: boolean }) {
  return (
    <div className={cn("grid grid-cols-[1fr_1.3fr_1.3fr] gap-2 border-t px-3 py-2", !ok && "bg-red-50")}>
      <span className={ok ? "text-muted-foreground" : "text-red-800"}>{label}</span>
      <span className={cn(!ok && "font-medium text-red-900")}>{form}</span>
      <span className={cn("flex items-center gap-1", !ok && "font-medium text-red-900")}>
        {bill ? (
          <>
            {bill}
            {ok ? <CheckIcon className="size-3.5 text-green-700" /> : <AlertTriangleIcon className="size-3.5" />}
          </>
        ) : (
          <span className="text-muted-foreground">-</span>
        )}
      </span>
    </div>
  );
}
