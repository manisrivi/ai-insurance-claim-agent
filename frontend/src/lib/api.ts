// api.ts: every call to the FastAPI backend lives here (one place to change URLs)

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type ClaimStatus = "processing" | "approved" | "rejected" | "officer_review";

export type Claim = {
  claim_id: string;
  patient_name: string;
  policy_number: string;
  hospital_name: string;
  treatment: string;
  admission_date: string;
  discharge_date: string;
  amount: number;
  description: string | null;
  status: ClaimStatus;
  // Safe text for customers (fraud checks and AI notes stay internal)
  message: string;
  officer_note: string | null;
  created_at: string;
  updated_at: string;
};

export type BillDetails = {
  patient_name: string | null;
  hospital_name: string | null;
  treatment: string | null;
  admission_date: string | null;
  discharge_date: string | null;
  total_amount: number | null;
};

// Officers also get the risk level, the AI notes and what the AI read from the bill
export type OfficerClaim = Claim & {
  risk: "low" | "high" | null;
  reason: string | null;
  extracted_details: Partial<BillDetails> | null;
};

export type ClaimCreated = { claim_id: string; status: ClaimStatus; message: string };

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

// FastAPI errors: "detail" is a string (400/404) or a list of field errors (422)
async function readError(res: Response): Promise<ApiError> {
  let message = "Something went wrong. Try again.";
  try {
    const body = await res.json();
    if (typeof body.detail === "string") {
      message = body.detail;
    } else if (Array.isArray(body.detail) && body.detail.length > 0) {
      message = String(body.detail[0].msg).replace(/^Value error, /, "");
    }
  } catch {
    // body was not JSON; keep the default message
  }
  return new ApiError(res.status, message);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { cache: "no-store", ...init });
  } catch {
    throw new ApiError(0, "Can't reach the server. Is the backend running?");
  }
  if (!res.ok) throw await readError(res);
  return res.json() as Promise<T>;
}

// ---------- Customer ----------

export function submitClaim(form: FormData) {
  // FormData = form fields + the PDF file (browser sets the multipart header itself)
  return request<ClaimCreated>("/claims", { method: "POST", body: form });
}

export function getClaim(claimId: string) {
  return request<Claim>(`/claims/${encodeURIComponent(claimId)}`);
}

export function searchByPolicy(policyNumber: string, patientName: string) {
  // Both are needed: a policy number alone must not reveal anyone's claims
  const params = new URLSearchParams({ policy_number: policyNumber, patient_name: patientName });
  return request<Claim[]>(`/claims?${params}`);
}

// ---------- Officer ----------

function officerHeaders(key: string) {
  return { "X-Officer-Key": key, "Content-Type": "application/json" };
}

export function getOfficerClaims(key: string) {
  return request<OfficerClaim[]>("/officer/claims", { headers: officerHeaders(key) });
}

export function decideClaim(key: string, claimId: string, decision: "approved" | "rejected", note: string) {
  return request<Claim>(`/officer/claims/${encodeURIComponent(claimId)}/decision`, {
    method: "POST",
    headers: officerHeaders(key),
    body: JSON.stringify({ decision, note: note.trim() || null }),
  });
}
