-- Corvana knowledge layer: derived logic. Hand-written. Tables and enum types are in 010_tables.sql, which is
-- generated from model/schema.dbml; row-level security is in 030_security.sql. No table definitions here.
--
-- Every view is security_invoker and every function security invoker, so row-level security applies to the
-- asking user (the tools SET ROLE to that user). The one exception, hidden_newer_count, is security definer on
-- purpose and leaks a count only.
--
-- as_of means "as known at". A row counts for an as-of date when its business date (as_of, as_of_date,
-- action_date, published_at) is on or before that date AND it had arrived by then: updated_on <= known_by(as_of).
-- Business date orders the rows; arrival date gates what is visible, so a back-dated row delivered later never
-- changes an earlier answer. The base pack is the earliest knowledge the layer has, so for a date before the base
-- load known_by() returns the base load date: such a date reads the base pack by business date, as before.

-- ---------------------------------------------------------------------------------------------------------------
-- Extensions and indexes the DBML can only name. fuzzystrmatch (trusted, ships with Postgres) gives levenshtein()
-- for the nearest-match hint on unresolved positions; GIN on the array columns searched with = any() / &&.
-- ---------------------------------------------------------------------------------------------------------------

create extension if not exists fuzzystrmatch;

create index documents_about_issuers_gin     on documents   using gin (about_issuers);
create index documents_about_instruments_gin on documents   using gin (about_instruments);
create index issuers_aliases_gin             on issuers     using gin (aliases);
create index instruments_aliases_gin         on instruments using gin (aliases);
create index instruments_description_lower   on instruments (lower(description));

-- The arrival cut-off for an as-of date: the date itself, or the base load date (the earliest updated_on in
-- sources, written by kl-load) when the date is earlier than the base load.
create function known_by(p_as_of date) returns date language sql stable security invoker as $$
    select greatest(p_as_of, (select min(updated_on) from sources))
$$;

-- ---------------------------------------------------------------------------------------------------------------
-- alias: the one name lookup. Every name column and every aliases[] element of the four entity tables, plus the
-- ids themselves and the currency codes found on country, instruments and curves. name_column says which column
-- the name came from (the tools use it to say "identifier" vs "alias"). Uniqueness of (entity_type, lower(alias))
-- is checked by validate.py: an array column cannot carry a unique index across its elements. A description is a
-- name only when no other instrument carries the same one (a RegS/144A pair shares it): it is free text, not an
-- identifier, so a shared description is left out rather than reported as an alias collision.
-- ---------------------------------------------------------------------------------------------------------------

create view alias with (security_invoker = true) as
select 'issuer'::text as entity_type, issuer_id as entity_id, legal_name as alias, 'legal_name'::text as name_column
from issuers
union all select 'issuer', issuer_id, short_name, 'short_name' from issuers where short_name is not null
union all select 'issuer', issuer_id, a, 'aliases' from issuers, unnest(aliases) as a
union all select 'issuer', issuer_id, issuer_id, 'id' from issuers
union all select 'instrument', instrument_id, ticker, 'ticker' from instruments
union all select 'instrument', instrument_id, isin::text, 'isin' from instruments where isin is not null
union all select 'instrument', i.instrument_id, i.description, 'description' from instruments i
          where i.description is not null
            and not exists (select 1 from instruments j where lower(j.description) = lower(i.description)
                                                          and j.instrument_id <> i.instrument_id)
union all select 'instrument', instrument_id, a, 'aliases' from instruments, unnest(aliases) as a
union all select 'instrument', instrument_id, instrument_id, 'id' from instruments
union all select 'curve', curve_id, curve_id, 'curve_id' from curves
union all select 'curve', curve_id, a, 'aliases' from curves, unnest(aliases) as a
union all select 'country', code::text, name, 'name' from country
union all select 'country', code::text, a, 'aliases' from country, unnest(aliases) as a
union all select 'country', code::text, code::text, 'id' from country
union all select distinct 'currency', c, c, 'currency'
from (select currency::text from country where currency is not null
      union select currency::text from instruments
      union select currency::text from curves) as x(c);

-- Reliability words -> a 3-tier rank used by the precedence rule. Deliberately coarse.
create view source_tier with (security_invoker = true) as
select source_id,
       case when reliability ilike 'high%'   then 3
            when reliability ilike 'medium%' then 2
            else 1 end as tier
from sources;

-- Positions joined to instruments by the identifier kind the OMS says it used. Unresolved rows keep instrument_id
-- null. instrument_updated_on lets a point-in-time query treat an instrument delivered later as unknown then.
create view position_resolved with (security_invoker = true) as
select p.*, i.instrument_id, i.description as instrument_description, i.instrument_type,
       i.updated_on as instrument_updated_on
from positions p
left join instruments i
  on case p.ref_type when 'ISIN' then i.isin::text when 'INTERNAL' then i.instrument_id when 'TICKER' then i.ticker end
     = p.instrument_ref;

-- The positions as of a date: per book, the latest position date on or before p_as_of among rows known by then.
-- Per book, so a delivery that carries one book leaves every other book at its own latest date. A book whose
-- positions are all closed needs a delivery that says so; an absent book is read as unchanged.
create function positions_as_of(p_as_of date) returns setof position_resolved
language sql stable security invoker as $$
    select p.* from position_resolved p
    where p.updated_on <= known_by(p_as_of)
      and p.as_of_date = (select max(q.as_of_date) from positions q
                          where q.book = p.book and q.as_of_date <= p_as_of and q.updated_on <= known_by(p_as_of))
$$;

-- Latest ratings row per resolved issuer and agency, with the scale rank attached.
create view rating_current with (security_invoker = true) as
select distinct on (r.issuer_id, r.agency) r.*, s.rank
from ratings r
join rating_scale s on s.agency = r.agency and s.rating = r.rating
where r.issuer_id is not null
order by r.issuer_id, r.agency, r.action_date desc;

-- A numeric as comparison text, scale-insensitive: 51.00 and 51.0000 compare equal.
create function num_key(n numeric) returns text language sql immutable as $$
    select case when n is null then ''
                when position('.' in n::text) > 0 then rtrim(rtrim(n::text, '0'), '.')
                else n::text end
$$;

-- ---------------------------------------------------------------------------------------------------------------
-- edges: the whole graph. statements rows plus every level-1 link projected to the statement shape with a
-- synthetic edge_id. A level-1 edge's quote is the raw name column as the source wrote it; its status is
-- REFERENCE when that raw name is the resolved entity's legal name and INFERRED when a curated alias did the
-- resolving. Columns with no raw name (currency, curve, country) are REFERENCE and quote the column name.
-- OWNS edges from the tracker are REFERENCE by the ownership table's definition (model/schema.dbml), tier 2.
-- method is null on level-1 edges: a file value is an edge, not a derived row. known_on is the arrival date
-- (updated_on of the row behind the edge; for a resolved link, the later of the two rows, so a name resolved
-- when its entity arrived is not visible before then); every as-of reader gates on known_on <= known_by(as_of).
-- ---------------------------------------------------------------------------------------------------------------

create view edges with (security_invoker = true) as
select s.statement_id, 'stmt:' || s.statement_id as edge_id,
       s.subject_type, s.subject_id, s.predicate, s.object_type, s.object_id,
       s.value_num, s.value_text, s.holds, s.as_of, s.source_system, s.source_file, s.document_id,
       s.quote, s.method::text as method, s.status::text as status, s.visibility, t.tier,
       s.updated_on as known_on
from statements s
join source_tier t on t.source_id = s.source_system
union all
select null, 'instruments:' || i.instrument_id || ':issuer_id', 'instrument', i.instrument_id,
       case when i.instrument_type = 'CDS' then 'REFERENCES_CREDIT' else 'ISSUED_BY' end, 'issuer', i.issuer_id,
       null, null, true, i.updated_on, i.source_system, i.source_file, null,
       i.issuer_name, null,
       case when lower(i.issuer_name) = lower(o.legal_name) then 'REFERENCE' else 'INFERRED' end, null, t.tier, greatest(i.updated_on, o.updated_on)
from instruments i
join issuers o on o.issuer_id = i.issuer_id
join source_tier t on t.source_id = i.source_system
union all
select null, 'instruments:' || i.instrument_id || ':guarantor_id', 'instrument', i.instrument_id,
       'GUARANTEED_BY', 'issuer', i.guarantor_id,
       null, null, true, i.updated_on, i.source_system, i.source_file, null,
       i.guarantor_name, null,
       case when lower(i.guarantor_name) = lower(o.legal_name) then 'REFERENCE' else 'INFERRED' end, null, t.tier, greatest(i.updated_on, o.updated_on)
from instruments i
join issuers o on o.issuer_id = i.guarantor_id
join source_tier t on t.source_id = i.source_system
union all
select null, 'ownership:' || w.ownership_id, 'issuer', w.owner_id, 'OWNS', 'issuer', w.owned_id,
       w.stake_pct, w.source || coalesce('; ' || w.notes, ''), true, w.as_of_date,
       'OwnershipTracker', w.source_file, null,
       w.owner || ' -> ' || w.owned_entity || ' ' || num_key(w.stake_pct) || '% (' || coalesce(w.source, 'no source') || ')',
       null, 'REFERENCE', null, t.tier, greatest(w.updated_on, ow.updated_on, od.updated_on)
from ownership w
join issuers ow on ow.issuer_id = w.owner_id
join issuers od on od.issuer_id = w.owned_id
join source_tier t on t.source_id = 'OwnershipTracker'
where w.owner_id is not null and w.owned_id is not null
union all
select null, 'instruments:' || i.instrument_id || ':currency', 'instrument', i.instrument_id,
       'DENOMINATED_IN', 'currency', i.currency::text,
       null, null, true, i.updated_on, i.source_system, i.source_file, null,
       'instruments.currency', null, 'REFERENCE', null, t.tier, i.updated_on
from instruments i
join source_tier t on t.source_id = i.source_system
union all
select null, 'instruments:' || i.instrument_id || ':underlying_curve', 'instrument', i.instrument_id,
       'PRICED_OFF', 'curve', i.underlying_curve,
       null, null, true, i.updated_on, i.source_system, i.source_file, null,
       'instruments.underlying_curve', null, 'REFERENCE', null, t.tier, i.updated_on
from instruments i
join source_tier t on t.source_id = i.source_system
where i.underlying_curve is not null
union all
select null, 'curves:' || c.curve_id || ':currency', 'curve', c.curve_id, 'DENOMINATED_IN', 'currency', c.currency::text,
       null, null, true, c.updated_on, c.source_system, c.source_file, null,
       'curves.currency', null, 'REFERENCE', null, t.tier, c.updated_on
from curves c
join source_tier t on t.source_id = c.source_system
union all
select null, 'country:' || c.code || ':currency', 'currency', c.currency::text, 'CURRENCY_OF', 'country', c.code::text,
       null, null, true, c.updated_on, 'Curated', 'curation/countries.yaml', null,
       'country.currency', null, 'REFERENCE', null, t.tier, c.updated_on
from country c
join source_tier t on t.source_id = 'Curated'
where c.currency is not null
union all
select null, 'country:' || c.code || ':sovereign_issuer_id', 'country', c.code::text, 'SOVEREIGN_IS', 'issuer',
       c.sovereign_issuer_id,
       null, null, true, c.updated_on, 'Curated', 'curation/countries.yaml', null,
       'country.sovereign_issuer_id', null, 'REFERENCE', null, t.tier, c.updated_on
from country c
join source_tier t on t.source_id = 'Curated'
where c.sovereign_issuer_id is not null;

-- ---------------------------------------------------------------------------------------------------------------
-- Precedence: for each link, every visible edge true on or before p_as_of, ranked. rn = 1 is the current value.
-- Rank: status first (CONFIRMED by a person 3, REFERENCE and INFERRED 2, PROPOSED 1; REJECTED excluded), then
-- source tier, then the latest as_of, then edge_id. A confirmation therefore overrides a reference-grade row;
-- without one, reference data outranks documents regardless of date. high_tier (REFERENCE, INFERRED, CONFIRMED)
-- stays for link_quality's CONFLICT test and the hop grade in exposure_paths. Level-1 edges and statements
-- compete on the same link: the tracker's 51 (edge) and the IPO note's 34 (statement). p_link_key (optional)
-- restricts the ranking to one link, for callers that need one link only (the ingest's contradiction guard).
-- ---------------------------------------------------------------------------------------------------------------

create function current_statements(p_as_of date, p_link_key text default null)
returns table (
    edge_id text, statement_id int, link_key text, rn bigint, high_tier boolean, compare_key text,
    subject_type text, subject_id text, predicate text, object_type text, object_id text,
    value_num numeric, value_text text, holds boolean, as_of date, source_system text, source_file text,
    document_id int, quote text, method text, status text, visibility text, tier int
) language sql stable security invoker as $$
    with ranked as (
        select e.subject_type || '|' || e.subject_id || '|' || e.predicate || '|' ||
                   case when d.single_valued then '' else e.object_id end as link_key,
               e.status in ('REFERENCE', 'INFERRED', 'CONFIRMED') as high_tier,
               case e.status when 'CONFIRMED' then 3 when 'REFERENCE' then 2 when 'INFERRED' then 2 else 1 end
                   as status_rank,
               case d.compare when 'object'    then e.object_id
                              when 'value_num' then num_key(e.value_num)
                              when 'holds'     then e.holds::text end as compare_key,
               e.*
        from edges e
        join predicate_def d on d.predicate = e.predicate
        where e.as_of <= p_as_of and e.known_on <= known_by(p_as_of) and e.status <> 'REJECTED'
          and (p_link_key is null
               or e.subject_type || '|' || e.subject_id || '|' || e.predicate || '|' ||
                  case when d.single_valued then '' else e.object_id end = p_link_key)
    )
    select edge_id, statement_id, link_key,
           row_number() over (partition by link_key order by status_rank desc, tier desc, as_of desc, edge_id desc) as rn,
           high_tier, compare_key,
           subject_type, subject_id, predicate, object_type, object_id, value_num, value_text, holds, as_of,
           source_system, source_file, document_id, quote, method, status, visibility, tier
    from ranked
$$;

-- Disagreement and agreement between the winner of a link and every other visible edge on it. A row that agrees
-- with the winner is CORROBORATED. When the winner is CONFIRMED a person has settled the link, so every other
-- row is SUPERSEDED. An older row from the winner's own source is SUPERSEDED too: the source updated itself (the
-- tracker's 51 replaced by its 34). CONFLICT is reserved for reference-grade disagreements between sources that
-- no person has ruled on.
create function link_quality(p_as_of date)
returns table (kind text, link_key text, winner_edge text, other_edge text, message text)
language sql stable security invoker as $$
    with c as (select * from current_statements(p_as_of)),
         w as (select * from c where rn = 1)
    select case when o.compare_key = w.compare_key then 'CORROBORATED'
                when w.status = 'CONFIRMED' then 'SUPERSEDED'
                when o.source_system = w.source_system and o.as_of < w.as_of then 'SUPERSEDED'
                when o.high_tier and w.high_tier then 'CONFLICT'
                when o.as_of > w.as_of then 'STALE'
                when o.as_of = w.as_of then 'CONFLICT'
                else 'SUPERSEDED' end as kind,
           w.link_key, w.edge_id, o.edge_id,
           format('%s %s %s: current %s (%s, %s, as_of %s) vs %s (%s, %s, as_of %s)',
                  w.subject_id, w.predicate, w.object_id,
                  w.compare_key, w.status, w.source_system, w.as_of,
                  o.compare_key, o.status, o.source_system, o.as_of)
    from w
    join c o on o.link_key = w.link_key and o.edge_id <> w.edge_id
$$;

-- Everything a reviewer should look at as of a date, for the asking user's visible rows: link quality plus
-- UNRESOLVED_REF (a position that matches no instrument known on that date; the message names a known ISIN or
-- internal id one edit away when there is one, and says it was not applied), UNRESOLVED_NAME (a level-1 name
-- column that resolved to no id, or to an entity that arrived after the date), UNLABELLED_DOCUMENT, UNKNOWN_LABEL (a document label granted to no user),
-- UNKNOWN_BOOK (a book granted to no user), RATING_LAG (an issuer rated above its guarantor by the same agency;
-- one flag per agency that rates both, subject '<issuer>|GUARANTEED_BY|<guarantor>|<agency>'). Both UNKNOWN kinds
-- are rows no user can see, so they show only to the admin role (the ingest report, the validator).
create function data_quality(p_as_of date)
returns table (kind text, subject text, edge_id text, other_edge_id text, message text)
language sql stable security invoker as $$
    select kind, link_key, winner_edge, other_edge, message
    from link_quality(p_as_of)
    union all
    select 'UNRESOLVED_REF', p.book || '|' || p.instrument_ref, null, null,
           format('position %s/%s (%s) matches no instrument known on %s', p.book, p.instrument_ref, p.ref_type, p_as_of)
           || case when near.instrument_id is null then ''
              else format('; nearest known %s %s (%s); not applied', p.ref_type, near.ident, near.instrument_id) end
    from positions_as_of(p_as_of) p
    -- the hint: a known identifier of the same kind (ISIN or INTERNAL) one edit away; never used to resolve
    left join lateral (
        select i.instrument_id, case p.ref_type when 'ISIN' then i.isin::text else i.instrument_id end as ident
        from instruments i
        where p.ref_type in ('ISIN', 'INTERNAL') and i.updated_on <= known_by(p_as_of)
          and levenshtein(p.instrument_ref, case p.ref_type when 'ISIN' then i.isin::text else i.instrument_id end) = 1
        order by 2 limit 1) near on true
    where p.instrument_id is null or p.instrument_updated_on > known_by(p_as_of)
    union all
    select 'UNRESOLVED_NAME', 'instruments|' || instrument_id || '|issuer_name', null, null,
           format('instruments %s issuer_name %L resolves to no issuer', instrument_id, issuer_name)
    from instruments i where i.issuer_name is not null and i.updated_on <= known_by(p_as_of)
      and (i.issuer_id is null or exists (select 1 from issuers o where o.issuer_id = i.issuer_id and o.updated_on > known_by(p_as_of)))
    union all
    select 'UNRESOLVED_NAME', 'instruments|' || instrument_id || '|guarantor_name', null, null,
           format('instruments %s guarantor_name %L resolves to no issuer', instrument_id, guarantor_name)
    from instruments i where i.guarantor_name is not null and i.updated_on <= known_by(p_as_of)
      and (i.guarantor_id is null or exists (select 1 from issuers o where o.issuer_id = i.guarantor_id and o.updated_on > known_by(p_as_of)))
    union all
    select 'UNRESOLVED_NAME', 'ownership|' || ownership_id || '|owner', null, null,
           format('ownership row %s owner %L resolves to no issuer', ownership_id, owner)
    from ownership w where w.updated_on <= known_by(p_as_of)
      and (w.owner_id is null or exists (select 1 from issuers o where o.issuer_id = w.owner_id and o.updated_on > known_by(p_as_of)))
    union all
    select 'UNRESOLVED_NAME', 'ownership|' || ownership_id || '|owned_entity', null, null,
           format('ownership row %s owned_entity %L resolves to no issuer', ownership_id, owned_entity)
    from ownership w where w.updated_on <= known_by(p_as_of)
      and (w.owned_id is null or exists (select 1 from issuers o where o.issuer_id = w.owned_id and o.updated_on > known_by(p_as_of)))
    union all
    select 'UNRESOLVED_NAME', 'ratings|' || entity || '|' || agency || '|' || action_date, null, null,
           format('ratings %L (%s, %s) resolves to no issuer', entity, agency, action_date)
    from ratings r where r.updated_on <= known_by(p_as_of)
      and (r.issuer_id is null or exists (select 1 from issuers o where o.issuer_id = r.issuer_id and o.updated_on > known_by(p_as_of)))
    union all
    select 'UNLABELLED_DOCUMENT', source_file || '|' || published_at, null, null,
           format('document %s has no visibility label and is hidden from everyone', source_file)
    from documents where visibility is null and updated_on <= known_by(p_as_of)
    union all
    select 'UNKNOWN_LABEL', d.source_file || '|' || d.published_at, null, null,
           format('document %s has visibility %L, which is granted to no user; hidden from everyone',
                  d.source_file, d.visibility)
    from documents d
    where d.visibility is not null and d.updated_on <= known_by(p_as_of)
      and not exists (select 1 from entitlements e where d.visibility = any(e.research_visibility))
    union all
    select 'UNKNOWN_BOOK', 'book|' || p.book, null, null,
           format('book %s (%s position rows) is granted to no user; hidden from everyone', p.book, count(*))
    from positions p
    where p.as_of_date <= p_as_of and p.updated_on <= known_by(p_as_of)
      and not exists (select 1 from entitlements e where p.book = any(e.books))
    group by p.book
    union all
    select 'RATING_LAG', g.subject_id || '|GUARANTEED_BY|' || g.object_id || '|' || rs.agency, g.edge_id, null,
           format('%s rated %s (rank %s) by %s is better than guarantor %s rated %s (rank %s)',
                  g.subject_id, rs.rating, rs.rank, rs.agency, g.object_id, rg.rating, rg.rank)
    from current_statements(p_as_of) g
    -- per agency: the subject's latest rating from each agency, compared with the guarantor's from the same agency
    join lateral (select distinct on (r.agency) r.agency, r.rating, s.rank from ratings r
                  join rating_scale s on s.agency = r.agency and s.rating = r.rating
                  where r.issuer_id = g.subject_id and r.action_date <= p_as_of and r.updated_on <= known_by(p_as_of)
                  order by r.agency, r.action_date desc) rs on true
    join lateral (select r.rating, s.rank from ratings r
                  join rating_scale s on s.agency = r.agency and s.rating = r.rating
                  where r.issuer_id = g.object_id and r.agency = rs.agency and r.action_date <= p_as_of
                    and r.updated_on <= known_by(p_as_of)
                  order by r.action_date desc limit 1) rg on true
    where g.rn = 1 and g.predicate = 'GUARANTEED_BY' and g.subject_type = 'issuer' and g.holds and rs.rank < rg.rank
    order by 2
$$;

-- For people: the same as of today.
create view data_quality with (security_invoker = true) as
select * from data_quality(current_date);

-- Count of statements on a link that are newer than a date and that the asking user cannot see.
-- SECURITY DEFINER on purpose: it leaks a count, nothing else, so an answer can say "newer information exists".
-- Level-1 edges carry no visibility and are never counted. Inside a definer function current_user is the owner,
-- so the asker is read from the session, never from an argument: the role set by SET ROLE (the tools SET ROLE to
-- the user), else the session user. current_setting('role') keeps the SET ROLE value inside a definer function
-- (verified), and a role can only SET ROLE to a role it is a member of, so no caller can count for another user.
-- search_path is pinned and every name qualified: the body runs as the owner.
create function hidden_newer_count(p_subject_type text, p_subject_id text, p_predicate text, p_object_id text,
                                   p_after date, p_as_of date)
returns int language sql stable security definer set search_path = pg_catalog, public as $$
    select count(*)::int
    from public.statements s
    where s.subject_type = p_subject_type and s.subject_id = p_subject_id and s.predicate = p_predicate
      and (p_object_id is null or s.object_id = p_object_id)
      and s.as_of > p_after and s.as_of <= p_as_of and s.updated_on <= public.known_by(p_as_of)
      and s.status <> 'REJECTED' and s.visibility is not null
      and not exists (
          select 1 from pg_catalog.pg_roles r
          where r.rolname = 'vis_' || s.visibility
            and pg_catalog.pg_has_role(
                    coalesce(nullif(nullif(pg_catalog.current_setting('role', true), ''), 'none'),
                             session_user::text)::name,
                    r.oid, 'MEMBER'))
$$;

-- Research for a set of entities (the nodes on a user's exposure paths): the visible documents published on or
-- before p_as_of that are about at least one of them, ranked by how many of the given ids they are about, then
-- newest first, then document_id; capped at p_limit (null = no cap). about_on_path is the matched subset. Ids are
-- compared as plain text across the four about_* columns, which share no values (ISS-/INS- ids, curve ids, ISO
-- currency codes). The tools do no ranking of their own.
create function research_for_paths(p_entity_ids text[], p_as_of date, p_limit int default 10)
returns table (document_id int, source_system text, source_file text, kind text, title text, publisher text,
               author text, published_at timestamp, visibility text, text text, about_issuers text[],
               about_instruments text[], about_curves text[], about_currencies text[], topics text[],
               summary text, annotated_by text, about_on_path text[])
language sql stable security invoker as $$
    select d.document_id, d.source_system, d.source_file, d.kind::text, d.title, d.publisher, d.author,
           d.published_at, d.visibility, d.text, d.about_issuers, d.about_instruments, d.about_curves,
           d.about_currencies, d.topics, d.summary, d.annotated_by::text, m.ids
    from documents d
    cross join lateral (
        select array(select x from unnest(d.about_issuers || d.about_instruments || d.about_curves || d.about_currencies) x
                     where x = any(p_entity_ids) order by x) as ids) m
    where d.published_at < p_as_of + 1 and d.updated_on <= known_by(p_as_of) and cardinality(m.ids) > 0
    order by cardinality(m.ids) desc, d.published_at desc, d.document_id
    limit p_limit
$$;

-- ---------------------------------------------------------------------------------------------------------------
-- Path finding: every way an instrument is linked to a target entity, as of a date, through the edges the asking
-- user can see. One hop = one distinct (from, predicate, to) link; every edge on that link travels with the hop.
-- Direction comes from predicate_def (OWNS is walked from owned to owner). holds=false rows (denials) are never
-- walked; they surface through get_statements. A hop is "high" when at least one REFERENCE/INFERRED/CONFIRMED
-- edge supports it, else "low" (research or desk only).
-- Precedence on the walk (current_statements, as of the date): when a person has CONFIRMED a link's winner, only
-- the rows that agree with it are walked; the losers are SUPERSEDED and never make a hop of their own. Without a
-- confirmation every row is walked, so a document row that disagrees with reference data still shows as a
-- low-grade channel beside the winner (Meridian's desk QC vs the GB rule row: "unconfirmed", as the expected answers
-- require). A holds-compared link whose current winner is a denial (holds = false) is not walked at all.
-- p_start_ids (optional) restricts the walk to those instruments.
-- ---------------------------------------------------------------------------------------------------------------

create function exposure_paths(p_target_type text, p_target_id text, p_as_of date, p_max_depth int default 5,
                               p_start_ids text[] default null)
returns table (
    start_type text, start_id text, depth int,
    nodes text[],            -- 'type:id' per node, start first, target last
    predicates text[],       -- one per hop
    hop_grades text[],       -- 'high' | 'low' per hop
    hop_edge_ids text[]      -- comma-joined edge ids per hop, same order
) language sql stable security invoker as $$
    with recursive c as (
        select * from current_statements(p_as_of)
    ),
    w as (select link_key, compare_key, status, holds from c where rn = 1),
    walkable as (
        select c.*
        from c
        join w on w.link_key = c.link_key
        join predicate_def d on d.predicate = c.predicate
        where c.holds and c.object_id is not null
          and not (d.compare = 'holds' and not w.holds)                     -- a current denial blocks the link
          and (w.status <> 'CONFIRMED' or c.compare_key = w.compare_key)    -- a person settled it: winner's side only
    ),
    link as (
        select case d.direction when 'forward' then e.subject_type else e.object_type end as from_type,
               case d.direction when 'forward' then e.subject_id   else e.object_id   end as from_id,
               e.predicate,
               case d.direction when 'forward' then e.object_type  else e.subject_type end as to_type,
               case d.direction when 'forward' then e.object_id    else e.subject_id   end as to_id,
               string_agg(e.edge_id, ',' order by e.edge_id) as edge_ids,
               case when bool_or(e.high_tier) then 'high' else 'low' end as grade
        from walkable e
        join predicate_def d on d.predicate = e.predicate
        group by 1, 2, 3, 4, 5
    ),
    walk as (
        select 'instrument'::text as start_type, i.instrument_id as start_id, 0 as depth,
               array['instrument:' || i.instrument_id] as nodes,
               array[]::text[] as predicates, array[]::text[] as hop_grades, array[]::text[] as hop_edge_ids,
               'instrument'::text as cur_type, i.instrument_id as cur_id
        from instruments i
        where i.updated_on <= p_as_of and (p_start_ids is null or i.instrument_id = any (p_start_ids))
        union all
        select w.start_type, w.start_id, w.depth + 1,
               w.nodes || (l.to_type || ':' || l.to_id),
               w.predicates || l.predicate, w.hop_grades || l.grade, w.hop_edge_ids || l.edge_ids,
               l.to_type, l.to_id
        from walk w
        join link l on l.from_type = w.cur_type and l.from_id = w.cur_id
        where w.depth < p_max_depth
          and not (w.cur_type = p_target_type and w.cur_id = p_target_id)
          and not ((l.to_type || ':' || l.to_id) = any (w.nodes))
    )
    select start_type, start_id, depth, nodes, predicates, hop_grades, hop_edge_ids
    from walk
    where cur_type = p_target_type and cur_id = p_target_id
    order by start_id, depth, predicates
$$;
