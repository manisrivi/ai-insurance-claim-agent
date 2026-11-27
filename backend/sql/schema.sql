-- The claims register
create table if not exists claims (
    -- Internal ID (made by the database)
    id bigint generated always as identity primary key,
    -- Customer-friendly random ID made by the app: CLM-7F3K-Q9XA (unguessable)
    claim_id text not null unique,

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

-- Indexes that match how the app searches (upper/lower) and lists (status, date)
create index if not exists idx_claims_policy_upper on claims (upper(policy_number));
create index if not exists idx_claims_patient_lower on claims (lower(patient_name));
create index if not exists idx_claims_status_created on claims (status, created_at);
create index if not exists idx_claims_created on claims (created_at);

-- Supabase shares the "public" schema through its REST API.
-- RLS with no policies = that API sees nothing. The backend connects as the owner, so it still works.
alter table claims enable row level security;

-- The API also runs these on every start (and does the same for LangGraph's checkpoint tables).