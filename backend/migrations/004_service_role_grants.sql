-- Follow-up for hosted projects where 003 ran under Supabase's newer
-- default-privilege model. No data or schema objects are changed.

begin;

grant usage on schema public to service_role;
grant select, insert, update, delete on table
  public.import_batches,
  public.import_row_errors,
  public.mf_transactions,
  public.market_price_cache,
  public.price_sync_runs
to service_role;

commit;
