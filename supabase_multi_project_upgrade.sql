
-- Supabase project upgrade for multiple household projects.
-- Run this AFTER the original schema. It is safe to run multiple times.

create extension if not exists "pgcrypto";

create table if not exists public.household_projects (
    project_id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    project_name text not null default 'Home 1',
    project_type text default 'Home',
    is_active boolean default true,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

alter table public.household_projects enable row level security;

drop policy if exists "household_projects_select_own" on public.household_projects;
create policy "household_projects_select_own" on public.household_projects
for select using (auth.uid() = user_id);

drop policy if exists "household_projects_insert_own" on public.household_projects;
create policy "household_projects_insert_own" on public.household_projects
for insert with check (auth.uid() = user_id);

drop policy if exists "household_projects_update_own" on public.household_projects;
create policy "household_projects_update_own" on public.household_projects
for update using (auth.uid() = user_id);

alter table public.energy_scans
add column if not exists project_id uuid references public.household_projects(project_id) on delete set null;

alter table public.monthly_checkins
add column if not exists project_id uuid references public.household_projects(project_id) on delete set null;

create index if not exists idx_household_projects_user_id on public.household_projects(user_id);
create index if not exists idx_energy_scans_project_id on public.energy_scans(project_id);
create index if not exists idx_monthly_checkins_project_id on public.monthly_checkins(project_id);

insert into public.household_projects (user_id, project_name, project_type, is_active)
select distinct es.user_id, 'Home 1', 'Primary home', true
from public.energy_scans es
where es.project_id is null
and not exists (
    select 1 from public.household_projects hp
    where hp.user_id = es.user_id
);

update public.energy_scans es
set project_id = hp.project_id
from public.household_projects hp
where es.user_id = hp.user_id
and es.project_id is null;

update public.monthly_checkins mc
set project_id = hp.project_id
from public.household_projects hp
where mc.user_id = hp.user_id
and mc.project_id is null;
