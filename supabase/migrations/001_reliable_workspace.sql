-- Run in Supabase SQL Editor as the project owner. Back up existing data first.
-- Non-destructive: keeps existing rows and legacy text dates. A duplicate date
-- or duplicate (session_id,date) aborts this transaction instead of deleting data.
begin;

create table if not exists public.study_log (
  id bigint generated always as identity primary key,
  date text, period text, start_time text, end_time text, location text,
  task_type text, duration double precision, details text, mood text
);
create table if not exists public.reading_plan (
  id bigint generated always as identity primary key,
  create_date text, book_name text, plan_content text, actual_done text, status text
);
create table if not exists public.tasks (
  id bigint generated always as identity primary key,
  task_name text, status text, create_date text, deadline text, priority text
);
create table if not exists public.system_config (
  id integer primary key, system_name text, daily_motto text
);
create table if not exists public.current_status (
  id integer primary key, is_working boolean, start_time text,
  location text, task_type text, period text
);
create table if not exists public.inspirations (
  id bigint generated always as identity primary key,
  create_time text, content text, category text
);
create table if not exists public.daily_routines (
  id bigint generated always as identity primary key, date text not null,
  breakfast boolean not null default false, lunch boolean not null default false,
  dinner boolean not null default false, early_sleep boolean not null default false,
  early_wake boolean not null default false
);

alter table public.current_status add column if not exists session_id uuid;
alter table public.study_log add column if not exists session_id uuid;
update public.current_status set session_id = gen_random_uuid()
  where is_working is true and session_id is null;

insert into public.system_config (id, system_name, daily_motto)
values (1, 'Novawood''s Learning Space', '让每一次专注，都慢慢生长。') on conflict (id) do nothing;
insert into public.current_status (id, is_working) values (1, false) on conflict (id) do nothing;

create unique index if not exists routines_date_unique on public.daily_routines(date);
create unique index if not exists log_session_date_unique on public.study_log(session_id, date);
create index if not exists study_log_date_idx on public.study_log(date, id);
create index if not exists inspirations_time_idx on public.inspirations(create_time, id);
create index if not exists tasks_status_idx on public.tasks(status, id);
create index if not exists reading_status_idx on public.reading_plan(status, id);

-- New/updated rows are checked without rejecting old records at migration time.
do $$ begin
  if not exists (select 1 from pg_constraint where conname = 'task_name_nonempty' and conrelid = 'public.tasks'::regclass) then
    alter table public.tasks add constraint task_name_nonempty
      check (task_name is not null and length(btrim(task_name)) between 1 and 200) not valid;
    alter table public.tasks add constraint task_status_valid
      check (status is not null and status in ('待办', '已完成')) not valid;
  end if;
  if not exists (select 1 from pg_constraint where conname = 'book_name_nonempty' and conrelid = 'public.reading_plan'::regclass) then
    alter table public.reading_plan add constraint book_name_nonempty
      check (book_name is not null and length(btrim(book_name)) between 1 and 300) not valid;
    alter table public.reading_plan add constraint reading_status_valid
      check (status is not null and status in ('阅读中', '已读完')) not valid;
  end if;
  if not exists (select 1 from pg_constraint where conname = 'idea_nonempty' and conrelid = 'public.inspirations'::regclass) then
    alter table public.inspirations add constraint idea_nonempty
      check (content is not null and length(btrim(content)) between 1 and 5000) not valid;
  end if;
  if not exists (select 1 from pg_constraint where conname = 'duration_nonnegative' and conrelid = 'public.study_log'::regclass) then
    alter table public.study_log add constraint duration_nonnegative
      check (duration is not null and duration >= 0 and duration < 'Infinity'::double precision) not valid;
  end if;
end $$;

-- One private workspace: only the server-side service role may access its data.
-- No permissive anonymous policy is installed. A future multi-user version needs
-- user_id + Supabase Auth and per-user policies, not this single-owner model.
alter table public.study_log enable row level security;
alter table public.reading_plan enable row level security;
alter table public.tasks enable row level security;
alter table public.system_config enable row level security;
alter table public.current_status enable row level security;
alter table public.inspirations enable row level security;
alter table public.daily_routines enable row level security;
revoke all on public.study_log, public.reading_plan, public.tasks, public.system_config,
  public.current_status, public.inspirations, public.daily_routines from public, anon, authenticated;
grant select, insert, update, delete on public.study_log, public.reading_plan, public.tasks,
  public.system_config, public.current_status, public.inspirations, public.daily_routines to service_role;
do $$ declare seq text; tbl text; begin
  foreach tbl in array array['study_log','reading_plan','tasks','inspirations','daily_routines'] loop
    seq := pg_get_serial_sequence('public.' || tbl, 'id');
    if seq is not null then
      execute format('revoke all on sequence %s from public, anon, authenticated', seq);
      execute format('grant usage, select on sequence %s to service_role', seq);
    end if;
  end loop;
end $$;

create or replace function public.start_focus(
  p_session_id uuid, p_location text, p_task_type text, p_period text
) returns setof public.current_status
language plpgsql security invoker set search_path = '' as $$
declare current_row public.current_status;
begin
  if p_session_id is null or p_location is null or p_task_type is null or p_period is null
    or length(btrim(p_location)) not between 1 and 200
    or length(btrim(p_task_type)) not between 1 and 200
    or p_period not in ('上午','下午','晚上','深夜') then
    raise exception 'Invalid focus input';
  end if;
  select * into current_row from public.current_status where id = 1 for update;
  if not found then raise exception 'Workspace not initialized'; end if;
  if current_row.is_working then
    if current_row.session_id = p_session_id then return next current_row; return; end if;
    raise exception 'Another focus session is active. Refresh before retrying.';
  end if;
  if exists(select 1 from public.study_log where session_id = p_session_id) then
    raise exception 'This focus session is already completed';
  end if;
  return query update public.current_status set is_working = true, session_id = p_session_id,
    start_time = to_char(clock_timestamp() at time zone 'Asia/Shanghai', 'YYYY-MM-DD HH24:MI:SS'),
    location = btrim(p_location), task_type = btrim(p_task_type), period = p_period
    where id = 1 returning *;
end $$;

create or replace function public.finish_focus(p_session_id uuid, p_details text, p_mood text)
returns setof public.study_log
language plpgsql security invoker set search_path = '' as $$
declare
  current_row public.current_status;
  segment_start timestamp;
  segment_end timestamp;
  finish_time timestamp;
begin
  if p_session_id is null or length(coalesce(p_details,'')) > 5000 then
    raise exception 'Invalid finish input';
  end if;
  -- Both concurrent starts and finishes serialize on the same singleton row.
  select * into current_row from public.current_status where id = 1 for update;
  if not found then raise exception 'Workspace not initialized'; end if;
  if exists(select 1 from public.study_log where session_id = p_session_id) then
    return query select * from public.study_log where session_id = p_session_id order by date;
    return;
  end if;
  if current_row.is_working is not true or current_row.session_id is distinct from p_session_id then
    raise exception 'Focus session changed. Refresh before retrying.';
  end if;
  segment_start := current_row.start_time::timestamp;
  finish_time := clock_timestamp() at time zone 'Asia/Shanghai';
  if segment_start is null or segment_start > finish_time then
    raise exception 'Invalid focus start time';
  end if;
  while segment_start < finish_time loop
    segment_end := least(finish_time, date_trunc('day', segment_start) + interval '1 day');
    insert into public.study_log(date, period, start_time, end_time, location, task_type,
      duration, details, mood, session_id)
    values(to_char(segment_start, 'YYYY-MM-DD'), current_row.period,
      to_char(segment_start, 'YYYY-MM-DD HH24:MI:SS'), to_char(segment_end, 'YYYY-MM-DD HH24:MI:SS'),
      current_row.location, current_row.task_type,
      extract(epoch from (segment_end - segment_start)) / 3600.0,
      coalesce(p_details,''), p_mood, p_session_id);
    segment_start := segment_end;
  end loop;
  update public.current_status set is_working = false where id = 1;
  return query select * from public.study_log where session_id = p_session_id order by date;
end $$;

revoke all on function public.start_focus(uuid,text,text,text) from public, anon, authenticated;
revoke all on function public.finish_focus(uuid,text,text) from public, anon, authenticated;
grant execute on function public.start_focus(uuid,text,text,text) to service_role;
grant execute on function public.finish_focus(uuid,text,text) to service_role;
commit;
