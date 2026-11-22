-- Counter used to build Claim IDs (1, 2, 3...)
create sequence if not exists claim_number_seq;

-- The claims register
create table if not exists claims (
    -- Internal ID (made by the database)
    id bigint generated always as identity primary key,
    -- Customer-friendly ID, auto-built: CLM-2026-0001
    claim_id text not null unique
        default ('CLM-' || to_char(now(), 'YYYY') || '-' || lpad(nextval('claim_number_seq')::text, 4, '0')),

    -- Form fields from the customer
    patient_name text not null,
    policy_number text not null,
    hospital_name text not null,
    treatment text not null,
    admission_date date not null,
    discharge_date date not null,
    amount numeric(12, 2) not null check (amount > 0),
    description text,

    -- Filled by the AI agent
    bill_text text,
    extracted_details jsonb,

    -- Result of the AI / officer
    status text not null default 'processing'
        check (status in ('processing', 'approved', 'rejected', 'officer_review')),
    risk text check (risk in ('low', 'high')),
    reason text,
    officer_note text,

    -- Timestamps
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    -- Rule: discharge can't be before admission
    check (discharge_date >= admission_date)
);

-- Fast search by policy number and patient name
create index if not exists idx_claims_policy_number on claims (policy_number);
create index if not exists idx_claims_patient_name on claims (patient_name);