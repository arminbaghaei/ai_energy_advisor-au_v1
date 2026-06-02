
-- Supabase SQL schema for the personalised household energy dashboard
-- Run this in Supabase SQL Editor.

create extension if not exists "pgcrypto";

create table if not exists public.profiles (
    user_id uuid primary key references auth.users(id) on delete cascade,
    email text,
    household_nickname text default 'My Home',
    household_size text,
    tenure_type text,
    dwelling_type text,
    home_condition text,
    bill_problem text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create table if not exists public.energy_scans (
    scan_id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    created_at timestamptz default now(),
    monthly_bill numeric,
    annual_bill_estimate numeric,
    saving_low numeric,
    saving_high numeric,
    bill_problem text,
    home_condition text,
    dwelling_type text,
    score integer,
    result_category text,
    money_snapshot jsonb
);

create table if not exists public.answers (
    answer_id uuid primary key default gen_random_uuid(),
    scan_id uuid not null references public.energy_scans(scan_id) on delete cascade,
    user_id uuid not null references auth.users(id) on delete cascade,
    hotspot_key text,
    selected_answer text,
    is_correct boolean,
    points integer,
    created_at timestamptz default now()
);

create table if not exists public.recommendations (
    recommendation_id uuid primary key default gen_random_uuid(),
    scan_id uuid not null references public.energy_scans(scan_id) on delete cascade,
    user_id uuid not null references auth.users(id) on delete cascade,
    action_key text,
    title text,
    category text,
    cost_level text,
    impact_level text,
    priority integer,
    estimated_saving_low numeric,
    estimated_saving_high numeric,
    status text default 'Not started',
    created_at timestamptz default now()
);

create table if not exists public.monthly_checkins (
    checkin_id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    scan_id uuid references public.energy_scans(scan_id) on delete set null,
    checkin_month date not null,
    actual_bill numeric,
    comfort_rating integer,
    completed_actions text,
    notes text,
    created_at timestamptz default now()
);

alter table public.profiles enable row level security;
alter table public.energy_scans enable row level security;
alter table public.answers enable row level security;
alter table public.recommendations enable row level security;
alter table public.monthly_checkins enable row level security;

drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own" on public.profiles
for select using (auth.uid() = user_id);

drop policy if exists "profiles_insert_own" on public.profiles;
create policy "profiles_insert_own" on public.profiles
for insert with check (auth.uid() = user_id);

drop policy if exists "profiles_update_own" on public.profiles;
create policy "profiles_update_own" on public.profiles
for update using (auth.uid() = user_id);

drop policy if exists "energy_scans_select_own" on public.energy_scans;
create policy "energy_scans_select_own" on public.energy_scans
for select using (auth.uid() = user_id);

drop policy if exists "energy_scans_insert_own" on public.energy_scans;
create policy "energy_scans_insert_own" on public.energy_scans
for insert with check (auth.uid() = user_id);

drop policy if exists "answers_select_own" on public.answers;
create policy "answers_select_own" on public.answers
for select using (auth.uid() = user_id);

drop policy if exists "answers_insert_own" on public.answers;
create policy "answers_insert_own" on public.answers
for insert with check (auth.uid() = user_id);

drop policy if exists "recommendations_select_own" on public.recommendations;
create policy "recommendations_select_own" on public.recommendations
for select using (auth.uid() = user_id);

drop policy if exists "recommendations_insert_own" on public.recommendations;
create policy "recommendations_insert_own" on public.recommendations
for insert with check (auth.uid() = user_id);

drop policy if exists "recommendations_update_own" on public.recommendations;
create policy "recommendations_update_own" on public.recommendations
for update using (auth.uid() = user_id);

drop policy if exists "monthly_checkins_select_own" on public.monthly_checkins;
create policy "monthly_checkins_select_own" on public.monthly_checkins
for select using (auth.uid() = user_id);

drop policy if exists "monthly_checkins_insert_own" on public.monthly_checkins;
create policy "monthly_checkins_insert_own" on public.monthly_checkins
for insert with check (auth.uid() = user_id);
