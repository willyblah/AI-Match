# Scheduled Tasks (pg_cron + Edge Function, read on demand)

Use the official Supabase `pg_cron` pattern for any work that runs **on a time schedule** or **automatically after a condition is met**, with no user action driving it.

## ⚠️ REQUIRED FIRST: enable the extensions

Before scheduling anything, you **MUST** enable `pg_cron` and `pg_net` — nothing below works without them. Run this once up front:

```sql
-- Enable the pg_cron and pg_net extensions
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_net;
```

- `pg_cron` provides `cron.schedule` / `cron.job` / `cron.job_run_details`.
- `pg_net` provides `net.http_post` (needed to invoke an Edge Function from a cron job).

## ⚠️ REQUIRED: how to call an Edge Function from cron

When a cron job invokes an Edge Function via `net.http_post`, **you MUST read the URL and key from Vault** — never hardcode the project URL or any key.

**Calling an Edge Function is FORBIDDEN to use the service-role key.** Use the `publishable_key` (anon) in the `apikey` header, never the service-role key. If the task needs to encrypt/sign the payload, generate your own key yourself (store it in Vault and read it at call time) — do not repurpose the service-role key for that.

The two secrets (`project_url`, `publishable_key`) are **already pre-stored** in Vault — do **NOT** create them. At call time, read them with `select` from `vault.decrypted_secrets`. This exact format is mandatory:

```sql
select cron.schedule(
  'invoke-function-every-minute',
  '* * * * *', -- every minute
  $$
  select net.http_post(
      url := (select decrypted_secret from vault.decrypted_secrets where name = 'project_url') || '/functions/v1/function-name',
      headers := jsonb_build_object(
        'Content-type', 'application/json',
        'apikey', (select decrypted_secret from vault.decrypted_secrets where name = 'publishable_key')
      ),
      body := concat('{"time": "', now(), '"}')::jsonb
  ) as request_id;
  $$
);
```

- URL: `(select decrypted_secret from vault.decrypted_secrets where name = 'project_url') || '/functions/v1/<function-name>'`
- Auth header: `'apikey'` = `(select decrypted_secret from vault.decrypted_secrets where name = 'publishable_key')`
- Build `headers`/`body` with `jsonb_build_object`; the whole `net.http_post(...)` call goes inside a `$$ ... $$` body.

## Rules (always apply)

These hold for every scheduled task:

- Drive the work from `pg_cron`, never from frontend timers or a user opening a page.
- A cron job runs a Postgres function (or, via `pg_net`, an Edge Function) on a schedule — match the cron granularity to the requirement, do not poll more often than needed.
- Make the scan **idempotent**: a row must not be acted on twice (e.g. a `notified`/status guard, identical SELECT/UPDATE predicates, or optimistic locking).
- Verify after setup: the job is registered (`cron.job`) and has actually run (`cron.job_run_details`).
- Follow the responsibility split below.

## Responsibility Split (MUST follow)

- **Database (pg_cron + Postgres function)**: query rows, update state. Nothing else.
- **Edge Function**: side effects — push, email, third-party APIs (FCM, OpenAI, Stripe, WeChat, etc.).
- **NEVER** write notification / third-party logic in SQL.
- **NEVER** drive scheduled work from frontend timers or rely on a user opening a page.

Routing rule:

| Task type | Pattern |
|-----------|---------|
| Simple (delete expired rows, update stats, archive) | `Cron → Database Function` |
| Complex (send push/email, call external API, write back) | `Cron → Edge Function (via pg_net) → external API → write back` |

## Worked Example: todo reminder

The steps below are **one illustration**, not a fixed checklist — a real task may need only some of them (e.g. a pure cleanup job stops at Step 3 with a DB function; an in-app reminder skips the Edge Function). Take the pieces the task actually requires.

Example requirement: *create a todo → set a due time → remind 30 min / 1 h / 3 h before → push a notification when due.*

### Step 1 — Model the table

Carry the schedule and a `notified` guard on the row so the scan is idempotent.

```sql
create table todos (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null,
    title text not null,
    due_at timestamptz,
    notify_before_minutes int,          -- e.g. 30 = remind 30 min before due_at
    notified boolean default false,     -- guard: prevents duplicate sends
    created_at timestamptz default now()
);
```

### Step 2 — Create the database function

The function scans for due/matching rows and updates their state. Keep the SELECT and UPDATE predicates identical so a row is queued exactly once.

```sql
create function process_todo_notifications()
returns void
language plpgsql
as $$
begin
  insert into notification_queue (user_id, todo_id)
  select user_id, id
  from todos
  where notified = false
    and now() >= due_at - (notify_before_minutes || ' minutes')::interval;

  update todos
  set notified = true
  where notified = false
    and now() >= due_at - (notify_before_minutes || ' minutes')::interval;
end;
$$;
```

### Step 3 — Schedule the cron job

```sql
select cron.schedule(
  'todo-reminder',
  '* * * * *',                              -- every minute
  'select process_todo_notifications();'
);
```

- Cron expression is standard 5-field. Match the granularity to the requirement; do not poll more often than needed.
- Job names are unique; re-running `cron.schedule` with the same name updates the job.

### Step 4 — Deliver the notification (only if there is a side effect)

### Option A — DB-only (in-app reminders, unread badges)

`Cron → Postgres function → notification_queue`, client subscribes via Realtime. Suitable only when there is **no** external side effect.

### Option B — Edge Function (REQUIRED for push / email / external APIs)

Invoke an Edge Function from the cron job using `pg_net`; the function does the delivery.

```text
pg_cron → pg_net → Edge Function → FCM / email / external API → write back (notified = true)
```

Use the **REQUIRED Vault format** from the top of this doc (read `project_url` / `publishable_key` from `vault.decrypted_secrets` — never hardcode):

```sql
select cron.schedule(
  'todo-reminder',
  '* * * * *',
  $$
  select net.http_post(
      url := (select decrypted_secret from vault.decrypted_secrets where name = 'project_url') || '/functions/v1/send-reminders',
      headers := jsonb_build_object(
        'Content-type', 'application/json',
        'apikey', (select decrypted_secret from vault.decrypted_secrets where name = 'publishable_key')
      ),
      body := concat('{"time": "', now(), '"}')::jsonb
  ) as request_id;
  $$
);
```

The Edge Function queries due rows, sends the push/email, then marks `notified = true`. Authoring/deployment rules: see the **Edge Functions** section of `SKILL.md` (deploy with `supabase_deploy_edge_function`).

### Step 5 — Inspect & verify (per the verification rule above)

```sql
select * from cron.job;                                       -- registered jobs
select * from cron.job_run_details order by start_time desc;  -- execution history
```

## Recommended pattern for todo/reminder & SaaS

```text
todos
  → Cron (every minute)
  → Edge Function
  → query soon-due rows
  → send push / email
  → mark notified = true
```

This `pg_cron + Edge Function` split is the official Supabase recommendation and is the easiest to extend later — the database stays responsible only for querying and updating state, while all delivery logic lives in the Edge Function.

## Sources

- Scheduling Edge Functions — https://supabase.com/docs/guides/functions/schedule-functions
- Cron Quickstart — https://supabase.com/docs/guides/cron/quickstart
- Cron — https://supabase.com/docs/guides/cron
