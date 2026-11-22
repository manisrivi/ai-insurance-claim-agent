"use client";

import { ArrowRightIcon, BuildingIcon, FileUpIcon, ReceiptIcon, UserIcon, XIcon } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import { PageHero } from "@/components/site-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { ApiError, submitClaim } from "@/lib/api";

const MAX_PDF_MB = 5;

type Fields = {
  patient_name: string;
  policy_number: string;
  hospital_name: string;
  treatment: string;
  admission_date: string;
  discharge_date: string;
  amount: string;
  description: string;
};

const EMPTY: Fields = {
  patient_name: "", policy_number: "", hospital_name: "", treatment: "",
  admission_date: "", discharge_date: "", amount: "", description: "",
};

// Same rules as the backend (Pydantic), so users see mistakes before sending
function validate(f: Fields, bill: File | null): Partial<Record<keyof Fields | "bill", string>> {
  const errors: Partial<Record<keyof Fields | "bill", string>> = {};
  const today = new Date().toISOString().slice(0, 10);
  if (f.patient_name.trim().length < 2) errors.patient_name = "Enter the patient's name";
  if (f.policy_number.trim().length < 3) errors.policy_number = "Enter your policy number";
  if (f.hospital_name.trim().length < 2) errors.hospital_name = "Enter the hospital name";
  if (f.treatment.trim().length < 2) errors.treatment = "Enter the treatment";
  if (!f.admission_date) errors.admission_date = "Pick the admission date";
  else if (f.admission_date > today) errors.admission_date = "Can't be in the future";
  if (!f.discharge_date) errors.discharge_date = "Pick the discharge date";
  else if (f.admission_date && f.discharge_date < f.admission_date) errors.discharge_date = "Can't be before admission date";
  const amount = Number(f.amount);
  if (!f.amount || !(amount > 0)) errors.amount = "Enter an amount above 0";
  if (!bill) errors.bill = "Upload the hospital bill";
  else if (bill.type !== "application/pdf") errors.bill = "Only PDF files are allowed";
  else if (bill.size > MAX_PDF_MB * 1024 * 1024) errors.bill = `PDF must be smaller than ${MAX_PDF_MB} MB`;
  return errors;
}

export default function NewClaimPage() {
  const router = useRouter();
  const fileInput = useRef<HTMLInputElement>(null);
  const [fields, setFields] = useState<Fields>(EMPTY);
  const [bill, setBill] = useState<File | null>(null);
  const [errors, setErrors] = useState<ReturnType<typeof validate>>({});
  const [serverError, setServerError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function update(name: keyof Fields, value: string) {
    setFields((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
  }

  function pickFile(file: File | null) {
    setBill(file);
    setErrors((prev) => ({ ...prev, bill: undefined }));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const found = validate(fields, bill);
    setErrors(found);
    if (Object.keys(found).length > 0) return;

    const form = new FormData();
    Object.entries(fields).forEach(([key, value]) => {
      if (value.trim()) form.append(key, value.trim());
    });
    form.append("bill", bill as File);

    setSubmitting(true);
    setServerError("");
    try {
      const created = await submitClaim(form);
      // Reset the form: Next.js keeps this page's state alive for the next visit
      setFields(EMPTY);
      pickFile(null);
      if (fileInput.current) fileInput.current.value = "";
      setSubmitting(false);
      router.push(`/claims/${created.claim_id}?new=1`);
    } catch (err) {
      setServerError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
      setSubmitting(false);
    }
  }

  function field(name: keyof Fields, label: string, props: React.ComponentProps<"input"> = {}) {
    return (
      <div className="grid gap-1.5">
        <Label htmlFor={name}>{label}</Label>
        <Input
          id={name}
          value={fields[name]}
          onChange={(e) => update(name, e.target.value)}
          aria-invalid={Boolean(errors[name])}
          {...props}
        />
        {errors[name] && <p className="text-xs text-destructive">{errors[name]}</p>}
      </div>
    );
  }

  return (
    <>
      <PageHero title="Submit a health claim" subtitle="Fill in the details exactly as on your hospital bill." />
      <form onSubmit={handleSubmit} noValidate className="mx-auto w-full max-w-3xl space-y-7 px-4 py-8 sm:px-6">
        <section>
          <h2 className="mb-3 flex items-center gap-1.5 text-xs font-medium text-brand-600"><UserIcon className="size-4" /> Patient and policy</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {field("patient_name", "Patient name", { placeholder: "Ravi Kumar", autoComplete: "name" })}
            {field("policy_number", "Policy number", { placeholder: "HLT-2026-0042" })}
          </div>
        </section>

        <section>
          <h2 className="mb-3 flex items-center gap-1.5 text-xs font-medium text-brand-600"><BuildingIcon className="size-4" /> Hospital stay</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {field("hospital_name", "Hospital name", { placeholder: "Sunrise Multispecialty Hospital" })}
            {field("treatment", "Treatment", { placeholder: "Dengue fever" })}
            {field("admission_date", "Admission date", { type: "date" })}
            {field("discharge_date", "Discharge date", { type: "date" })}
          </div>
        </section>

        <section>
          <h2 className="mb-3 flex items-center gap-1.5 text-xs font-medium text-brand-600"><ReceiptIcon className="size-4" /> Bill</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {field("amount", "Amount (Rs)", { type: "number", inputMode: "decimal", min: 1, placeholder: "18500" })}
            {field("description", "Description (optional)", { placeholder: "Admitted with high fever", maxLength: 1000 })}
          </div>

          {/* PDF upload box (click or drag a file in) */}
          <label
            htmlFor="bill"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => { e.preventDefault(); pickFile(e.dataTransfer.files[0] ?? null); }}
            className={`mt-4 flex cursor-pointer flex-col items-center rounded-xl border-[1.5px] border-dashed p-6 text-center text-sm transition-colors hover:bg-brand-50 ${
              errors.bill ? "border-destructive bg-red-50" : "border-brand-200 bg-[#f4fbf8]"
            }`}
          >
            <FileUpIcon className="size-6 text-brand-600" />
            {bill ? (
              <span className="mt-1 flex items-center gap-2 font-medium text-brand-800">
                {bill.name} · {Math.max(1, Math.round(bill.size / 1024))} KB
                <button
                  type="button"
                  aria-label="Remove file"
                  onClick={(e) => { e.preventDefault(); pickFile(null); if (fileInput.current) fileInput.current.value = ""; }}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <XIcon className="size-4" />
                </button>
              </span>
            ) : (
              <span className="mt-1 font-medium text-brand-800">Click to upload or drag your bill here</span>
            )}
            <span className="text-xs text-muted-foreground">PDF only, max {MAX_PDF_MB} MB</span>
            <input
              ref={fileInput}
              id="bill"
              type="file"
              accept="application/pdf,.pdf"
              className="sr-only"
              onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
            />
          </label>
          {errors.bill && <p className="mt-1.5 text-xs text-destructive">{errors.bill}</p>}
        </section>

        {serverError && (
          <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">{serverError}</p>
        )}

        <div className="flex justify-end gap-2">
          <Button asChild variant="outline" className="border-brand-200 text-brand-800"><Link href="/">Cancel</Link></Button>
          <Button type="submit" disabled={submitting}>
            {submitting ? <><Spinner /> Submitting…</> : <>Submit claim <ArrowRightIcon /></>}
          </Button>
        </div>
      </form>
    </>
  );
}
