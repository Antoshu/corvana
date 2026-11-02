-- Corvana knowledge layer: entitlements. Hand-written. Tables are in 010_tables.sql (generated), logic in 020.
--
-- Roles template (created by the loader from entitlements.yaml, because role names are data, not schema):
--   create role <username> nologin;               one per user          e.g. alice
--   create role book_<book> nologin;              one per book          e.g. book_em_macro
--   create role vis_<label> nologin;              one per label         e.g. vis_credit_internal
--   grant book_<book> to <username>;              from entitlements.books
--   grant vis_<label> to <username>;              from entitlements.research_visibility
--   grant usage on schema public to <role>; grant select on all tables in schema public to <role>;
-- Memberships are made to match the file exactly on every load (grants added, extras revoked); validate.py checks.
-- The loader runs as the admin role, which owns the tables and bypasses RLS. The tools SET ROLE <username>.
--
-- pg_has_role by name errors on a missing role, so membership is tested through pg_roles.

alter table positions enable row level security;
alter table positions force row level security;
create policy positions_by_book on positions for select using (
    exists (select 1 from pg_roles r where r.rolname = 'book_' || lower(book) and pg_has_role(current_user, r.oid, 'MEMBER'))
);

alter table documents enable row level security;
alter table documents force row level security;
create policy documents_by_label on documents for select using (
    visibility is not null and
    exists (select 1 from pg_roles r where r.rolname = 'vis_' || visibility and pg_has_role(current_user, r.oid, 'MEMBER'))
);

-- statements.visibility is copied from the document at write time so this policy needs no join.
alter table statements enable row level security;
alter table statements force row level security;
create policy statements_by_label on statements for select using (
    visibility is null or
    exists (select 1 from pg_roles r where r.rolname = 'vis_' || visibility and pg_has_role(current_user, r.oid, 'MEMBER'))
);
