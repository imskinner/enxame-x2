-- Enxame ×2 — perfis, partidas e ranking.
-- Rode uma vez no SQL Editor do Supabase. Pode rodar de novo: tudo é idempotente.
--
-- Regra de ouro: o navegador nunca grava pontuação direto. Ele só chama
-- start_run() ao começar e finish_run() ao perder; o servidor mede o tempo
-- da partida e recusa pontuações impossíveis para a onda alcançada.

-- ================= Perfis (apelido público) =================
create table if not exists public.profiles (
  id uuid primary key references auth.users on delete cascade,
  nickname text not null
    check (nickname = btrim(nickname) and nickname ~ '^[A-Za-z0-9_ À-ÖØ-öø-ÿ]{3,16}$'),
  created_at timestamptz not null default now()
);
create unique index if not exists profiles_nickname_key on public.profiles (lower(nickname));

alter table public.profiles enable row level security;
drop policy if exists "perfis são públicos" on public.profiles;
drop policy if exists "cria o próprio perfil" on public.profiles;
drop policy if exists "edita o próprio perfil" on public.profiles;
create policy "perfis são públicos" on public.profiles for select using (true);
create policy "cria o próprio perfil" on public.profiles for insert to authenticated with check (id = auth.uid());
create policy "edita o próprio perfil" on public.profiles for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

-- ================= Partidas =================
create table if not exists public.runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users on delete cascade,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  score int, wave int, kills int, peak int,          -- in the march, wave holds the meters marched
  valid boolean not null default false,
  mode text not null default 'defense' check (mode in ('defense', 'march'))
);
alter table public.runs add column if not exists mode text not null default 'defense';
alter table public.runs add column if not exists contracts text; -- march contracts used, comma-separated ids (nofila, noref, fury, narrow, horde, lean)
create index if not exists runs_mode_valid_finished on public.runs (mode, finished_at, score desc) where valid;
create index if not exists runs_user_started on public.runs (user_id, started_at);
create index if not exists runs_valid_finished on public.runs (finished_at, score desc) where valid;

-- Sem políticas: ninguém lê ou grava a tabela direto, só pelas funções abaixo.
alter table public.runs enable row level security;
revoke all on public.runs from anon, authenticated;

-- ================= Economia: carteira e Quartel =================
-- Moedas vêm só do servidor: finish_run paga a run (moedas da pista validadas + bônus da pontuação, em dobro nas três
-- primeiras runs do dia, teto diário depois). O Quartel gasta moedas em melhorias permanentes com preço crescente e
-- reembolso total. Diamantes ficam reservados para a loja (docs/economia.md).
create table if not exists public.wallets (
  user_id uuid primary key references auth.users on delete cascade,
  coins int not null default 0 check (coins >= 0),
  gems int not null default 0 check (gems >= 0),
  earned_today int not null default 0,
  runs_today int not null default 0,
  day date not null default current_date,
  updated_at timestamptz not null default now()
);
alter table public.wallets enable row level security;
drop policy if exists "le a propria carteira" on public.wallets;
create policy "le a propria carteira" on public.wallets for select to authenticated using (user_id = auth.uid());
revoke insert, update, delete on public.wallets from anon, authenticated;

create table if not exists public.quartel (
  user_id uuid not null references auth.users on delete cascade,
  upgrade text not null check (upgrade in ('recrutas', 'alojamento', 'arsenal', 'disciplina', 'cornetas', 'bateria', 'alquimia')),
  level int not null default 0 check (level >= 0),
  spent int not null default 0,
  primary key (user_id, upgrade)
);
alter table public.quartel enable row level security;
drop policy if exists "le o proprio quartel" on public.quartel;
create policy "le o proprio quartel" on public.quartel for select to authenticated using (user_id = auth.uid());
revoke insert, update, delete on public.quartel from anon, authenticated;

create or replace function public.quartel_max(p_upgrade text) returns int language sql immutable as $$
  select case p_upgrade when 'recrutas' then 10 when 'alojamento' then 6 when 'arsenal' then 6 when 'disciplina' then 4
                        when 'cornetas' then 4 when 'bateria' then 4 when 'alquimia' then 1 else 0 end;
$$;
create or replace function public.quartel_price(p_upgrade text, p_level int) returns int language sql immutable as $$
  select round((case p_upgrade when 'recrutas' then 200 when 'alojamento' then 400 when 'arsenal' then 500 when 'disciplina' then 300
                               when 'cornetas' then 300 when 'bateria' then 300 when 'alquimia' then 3000 else 0 end) * power(1.15, p_level))::int;
$$;
drop function if exists public.get_wallet();
create or replace function public.get_wallet() returns table (coins int, gems int, upgrades json, heroes json, achievements text[])
language sql stable security definer set search_path = ''
as $$
  select coalesce(w.coins, 0), coalesce(w.gems, 0),
         coalesce((select json_object_agg(q.upgrade, q.level) from public.quartel q where q.user_id = auth.uid()), '{}'::json),
         coalesce((select json_object_agg(h.hero, h.level) from public.heroes h where h.user_id = auth.uid()), '{}'::json),
         coalesce((select array_agg(a.key) from public.achievements a where a.user_id = auth.uid()), '{}'::text[])
  from (select 1) x left join public.wallets w on w.user_id = auth.uid();
$$;
create or replace function public.buy_quartel(p_upgrade text) returns table (coins int, level int)
language plpgsql security definer set search_path = ''
as $$
declare lvl int; price int; have int;
begin
  if auth.uid() is null then raise exception 'not_authenticated'; end if;
  if public.quartel_max(p_upgrade) = 0 then raise exception 'unknown_upgrade'; end if;
  insert into public.wallets (user_id) values (auth.uid()) on conflict do nothing;
  insert into public.quartel (user_id, upgrade) values (auth.uid(), p_upgrade) on conflict do nothing;
  select q.level into lvl from public.quartel q where q.user_id = auth.uid() and q.upgrade = p_upgrade for update;
  if lvl >= public.quartel_max(p_upgrade) then raise exception 'maxed'; end if;
  price := public.quartel_price(p_upgrade, lvl);
  select w.coins into have from public.wallets w where w.user_id = auth.uid() for update;
  if have < price then raise exception 'not_enough_coins'; end if;
  update public.wallets set coins = public.wallets.coins - price, updated_at = now() where user_id = auth.uid();
  update public.quartel set level = public.quartel.level + 1, spent = public.quartel.spent + price where user_id = auth.uid() and upgrade = p_upgrade;
  return query select w.coins, lvl + 1 from public.wallets w where w.user_id = auth.uid();
end $$;
create or replace function public.refund_quartel() returns int
language plpgsql security definer set search_path = ''
as $$
declare back int; total int;
begin
  if auth.uid() is null then raise exception 'not_authenticated'; end if;
  select coalesce(sum(spent), 0) into back from public.quartel where user_id = auth.uid();
  delete from public.quartel where user_id = auth.uid();
  update public.wallets set coins = coins + back, updated_at = now() where user_id = auth.uid() returning coins into total;
  return coalesce(total, 0);
end $$;

-- Heróis: desbloqueio com moedas ou diamantes, níveis só com moedas. Conquistas: julgadas pelo finish_run, pagam
-- diamantes uma vez cada.
create table if not exists public.heroes (
  user_id uuid not null references auth.users on delete cascade,
  hero text not null check (hero in ('muralha', 'arqueira', 'ladrao')),
  level int not null default 1 check (level between 1 and 5),
  primary key (user_id, hero)
);
alter table public.heroes enable row level security;
drop policy if exists "le os proprios herois" on public.heroes;
create policy "le os proprios herois" on public.heroes for select to authenticated using (user_id = auth.uid());
revoke insert, update, delete on public.heroes from anon, authenticated;

create table if not exists public.achievements (
  user_id uuid not null references auth.users on delete cascade,
  key text not null,
  at timestamptz not null default now(),
  primary key (user_id, key)
);
alter table public.achievements enable row level security;
drop policy if exists "le as proprias conquistas" on public.achievements;
create policy "le as proprias conquistas" on public.achievements for select to authenticated using (user_id = auth.uid());
revoke insert, update, delete on public.achievements from anon, authenticated;

create or replace function public.hero_price(p_hero text, p_with text) returns int language sql immutable as $$
  select case when p_with = 'gems' then (case p_hero when 'muralha' then 60 when 'arqueira' then 80 when 'ladrao' then 50 else 0 end)
              else (case p_hero when 'muralha' then 2500 when 'arqueira' then 3000 when 'ladrao' then 2000 else 0 end) end;
$$;
create or replace function public.hero_level_price(p_level int) returns int language sql immutable as $$
  select round(400 * power(1.3, p_level - 2))::int; -- the price of reaching p_level (2 to 5)
$$;
create or replace function public.achievement_gems(p_key text) returns int language sql immutable as $$
  select case p_key when 'first_march' then 5 when 'boss1' then 10 when 'km2' then 10 when 'km5' then 20 when 'km8' then 30 when 'km12' then 40
                    when 'score100k' then 15 when 'score500k' then 30 when 'kills1k' then 10 when 'contracts3' then 25
                    when 'defense10' then 10 when 'defense20' then 20 else 0 end;
$$;
create or replace function public.buy_hero(p_hero text, p_with text) returns table (coins int, gems int)
language plpgsql security definer set search_path = ''
as $$
declare price int; have_c int; have_g int;
begin
  if auth.uid() is null then raise exception 'not_authenticated'; end if;
  if public.hero_price(p_hero, 'coins') = 0 then raise exception 'unknown_hero'; end if;
  if exists (select 1 from public.heroes h where h.user_id = auth.uid() and h.hero = p_hero) then raise exception 'owned'; end if;
  insert into public.wallets (user_id) values (auth.uid()) on conflict do nothing;
  select w.coins, w.gems into have_c, have_g from public.wallets w where w.user_id = auth.uid() for update;
  if p_with = 'gems' then
    price := public.hero_price(p_hero, 'gems');
    if have_g < price then raise exception 'not_enough_gems'; end if;
    update public.wallets set gems = public.wallets.gems - price, updated_at = now() where user_id = auth.uid();
  else
    price := public.hero_price(p_hero, 'coins');
    if have_c < price then raise exception 'not_enough_coins'; end if;
    update public.wallets set coins = public.wallets.coins - price, updated_at = now() where user_id = auth.uid();
  end if;
  insert into public.heroes (user_id, hero) values (auth.uid(), p_hero);
  return query select w.coins, w.gems from public.wallets w where w.user_id = auth.uid();
end $$;
create or replace function public.level_hero(p_hero text) returns table (coins int, level int)
language plpgsql security definer set search_path = ''
as $$
declare lvl int; price int; have int;
begin
  if auth.uid() is null then raise exception 'not_authenticated'; end if;
  select h.level into lvl from public.heroes h where h.user_id = auth.uid() and h.hero = p_hero for update;
  if lvl is null then raise exception 'not_owned'; end if;
  if lvl >= 5 then raise exception 'maxed'; end if;
  price := public.hero_level_price(lvl + 1);
  select w.coins into have from public.wallets w where w.user_id = auth.uid() for update;
  if coalesce(have, 0) < price then raise exception 'not_enough_coins'; end if;
  update public.wallets set coins = public.wallets.coins - price, updated_at = now() where user_id = auth.uid();
  update public.heroes set level = public.heroes.level + 1 where user_id = auth.uid() and hero = p_hero;
  return query select w.coins, lvl + 1 from public.wallets w where w.user_id = auth.uid();
end $$;
-- Grants one achievement to the caller if new, paying its gems; returns the gems paid (0 if already had).
create or replace function public.grant_achievement(p_key text) returns int
language plpgsql security definer set search_path = ''
as $$
declare paid int := 0;
begin
  insert into public.achievements (user_id, key) values (auth.uid(), p_key) on conflict do nothing;
  if found then
    paid := public.achievement_gems(p_key);
    update public.wallets set gems = public.wallets.gems + paid, updated_at = now() where user_id = auth.uid();
  end if;
  return paid;
end $$;

-- Missoes diarias e semanais, bau de fim de corrida. Tudo concedido pelo servidor a partir de partidas validas.
alter table public.wallets add column if not exists chests_today int not null default 0;

create table if not exists public.missions (
  user_id uuid not null references auth.users on delete cascade,
  period text not null,
  key text not null,
  progress int not null default 0,
  claimed boolean not null default false,
  primary key (user_id, period, key)
);
alter table public.missions enable row level security;
drop policy if exists "le as proprias missoes" on public.missions;
create policy "le as proprias missoes" on public.missions for select to authenticated using (user_id = auth.uid());
revoke insert, update, delete on public.missions from anon, authenticated;

-- A mission: target, reward (coins for daily, gems for weekly) and how it progresses ('sum' adds each run, 'max' keeps the best run).
create or replace function public.mission_def(p_key text) returns table (target int, coins int, gems int, how text)
language sql immutable as $$
  select v.target, v.coins, v.gems, v.how from (values
    ('d_runs2', 2, 60, 0, 'sum'),
    ('d_km3', 3000, 100, 0, 'max'),
    ('d_kills500', 500, 80, 0, 'sum'),
    ('d_boss2', 2, 100, 0, 'sum'),
    ('d_coins150', 150, 60, 0, 'sum'),
    ('d_wave8', 8, 80, 0, 'max'),
    ('d_contract', 1000, 100, 0, 'max'),
    ('d_troop200', 200, 80, 0, 'max'),
    ('d_relics3', 3, 80, 0, 'sum'),
    ('w_km8', 8000, 0, 15, 'max'),
    ('w_runs10', 10, 0, 10, 'sum'),
    ('w_kills5k', 5000, 0, 15, 'sum'),
    ('w_boss10', 10, 0, 20, 'sum'),
    ('w_wave15', 15, 0, 15, 'max'),
    ('w_score300k', 300000, 0, 20, 'max'),
    ('w_contracts3', 2000, 0, 20, 'max'),
    ('w_coins1k', 1000, 0, 10, 'sum')
  ) as v(key, target, coins, gems, how) where v.key = p_key;
$$;

-- 'd' = the UTC day, 'w' = the ISO week (UTC).
create or replace function public.mission_period(p_kind text) returns text language sql stable as $$
  select case when p_kind = 'd' then 'd' || to_char(now() at time zone 'utc', 'YYYY-MM-DD') else 'w' || to_char(now() at time zone 'utc', 'IYYY-IW') end;
$$;

-- The three missions of a period, picked from the pool by a hash of the period: everyone gets the same three.
create or replace function public.mission_keys(p_period text) returns text[] language plpgsql immutable as $$
declare pool text[]; picked text[] := '{}'; i int := 0; k text;
begin
  pool := case when left(p_period, 1) = 'd'
    then array['d_runs2', 'd_km3', 'd_kills500', 'd_boss2', 'd_coins150', 'd_wave8', 'd_contract', 'd_troop200', 'd_relics3']
    else array['w_km8', 'w_runs10', 'w_kills5k', 'w_boss10', 'w_wave15', 'w_score300k', 'w_contracts3', 'w_coins1k'] end;
  while coalesce(array_length(picked, 1), 0) < 3 and i < 60 loop
    k := pool[1 + (('x' || substr(md5(p_period || ':' || i), 1, 7))::bit(28)::int % array_length(pool, 1))];
    if not (k = any(picked)) then picked := picked || k; end if;
    i := i + 1;
  end loop;
  return picked;
end $$;

create or replace function public.get_missions()
returns table (period text, key text, progress int, target int, coins int, gems int, claimed boolean)
language plpgsql security definer set search_path = ''
as $$
declare per text; k text;
begin
  if auth.uid() is null then raise exception 'not_authenticated'; end if;
  foreach per in array array[public.mission_period('d'), public.mission_period('w')] loop
    foreach k in array public.mission_keys(per) loop
      return query
        select per, k, coalesce(m.progress, 0), d.target, d.coins, d.gems, coalesce(m.claimed, false)
        from public.mission_def(k) d
        left join public.missions m on m.user_id = auth.uid() and m.period = per and m.key = k;
    end loop;
  end loop;
end $$;

create or replace function public.claim_mission(p_period text, p_key text) returns table (coins int, gems int)
language plpgsql security definer set search_path = ''
as $$
declare d record; m public.missions;
begin
  if auth.uid() is null then raise exception 'not_authenticated'; end if;
  if p_period not in (public.mission_period('d'), public.mission_period('w')) then raise exception 'expired'; end if;
  if not (p_key = any(public.mission_keys(p_period))) then raise exception 'unknown_mission'; end if;
  select * into d from public.mission_def(p_key);
  select * into m from public.missions x where x.user_id = auth.uid() and x.period = p_period and x.key = p_key for update;
  if not found or m.progress < d.target then raise exception 'not_done'; end if;
  if m.claimed then raise exception 'claimed'; end if;
  update public.missions set claimed = true where user_id = auth.uid() and period = p_period and key = p_key;
  insert into public.wallets (user_id) values (auth.uid()) on conflict do nothing;
  update public.wallets set coins = public.wallets.coins + d.coins, gems = public.wallets.gems + d.gems, updated_at = now() where user_id = auth.uid();
  return query select w.coins, w.gems from public.wallets w where w.user_id = auth.uid();
end $$;

-- Applies one valid run to the current missions; returns the keys it completed (comma-separated) or null.
create or replace function public.mission_progress(p_mode text, p_meters int, p_wave int, p_kills int, p_bosses int, p_coins int, p_score int, p_peak int, p_ncon int, p_relics int)
returns text language plpgsql security definer set search_path = ''
as $$
declare per text; k text; v int; d record; cur int; nxt int; done text[] := '{}';
begin
  foreach per in array array[public.mission_period('d'), public.mission_period('w')] loop
    foreach k in array public.mission_keys(per) loop
      v := case k
        when 'd_runs2' then 1
        when 'w_runs10' then 1
        when 'd_km3' then case when p_mode = 'march' then p_meters else 0 end
        when 'w_km8' then case when p_mode = 'march' then p_meters else 0 end
        when 'd_kills500' then p_kills
        when 'w_kills5k' then p_kills
        when 'd_boss2' then p_bosses
        when 'w_boss10' then p_bosses
        when 'd_coins150' then p_coins
        when 'w_coins1k' then p_coins
        when 'd_wave8' then case when p_mode = 'defense' then p_wave else 0 end
        when 'w_wave15' then case when p_mode = 'defense' then p_wave else 0 end
        when 'd_contract' then case when p_mode = 'march' and p_ncon >= 1 then p_meters else 0 end
        when 'w_contracts3' then case when p_mode = 'march' and p_ncon >= 3 then p_meters else 0 end
        when 'd_troop200' then case when p_mode = 'march' then p_peak else 0 end
        when 'w_score300k' then case when p_mode = 'march' then p_score else 0 end
        when 'd_relics3' then p_relics
        else 0 end;
      if v <= 0 then continue; end if;
      select * into d from public.mission_def(k);
      insert into public.missions (user_id, period, key, progress) values (auth.uid(), per, k, 0) on conflict do nothing;
      select x.progress into cur from public.missions x where x.user_id = auth.uid() and x.period = per and x.key = k for update;
      nxt := case when d.how = 'sum' then least(cur + v, d.target) else greatest(cur, least(v, d.target)) end;
      if nxt <> cur then
        update public.missions set progress = nxt where user_id = auth.uid() and period = per and key = k;
        if nxt >= d.target then done := done || k; end if;
      end if;
    end loop;
  end loop;
  return nullif(array_to_string(done, ','), '');
end $$;

-- ---------- weekly ranking prizes ----------
create table if not exists public.week_rewards (
  user_id uuid not null references auth.users on delete cascade,
  week text not null,
  mode text not null,
  rank int not null,
  gems int not null,
  claimed boolean not null default false,
  primary key (user_id, week, mode)
);
alter table public.week_rewards enable row level security;
drop policy if exists "le os proprios premios" on public.week_rewards;
create policy "le os proprios premios" on public.week_rewards for select to authenticated using (user_id = auth.uid());
revoke insert, update, delete on public.week_rewards from anon, authenticated;

create table if not exists public.weeks_settled (
  week text primary key,
  settled_at timestamptz not null default now()
);
alter table public.weeks_settled enable row level security;
revoke all on public.weeks_settled from anon, authenticated;

create or replace function public.week_gems(p_rank int) returns int language sql immutable as $$
  select case when p_rank = 1 then 25 when p_rank <= 10 then 12 when p_rank <= 100 then 5 when p_rank <= 1000 then 2 else 0 end;
$$;
create or replace function public.week_key(p_at timestamptz) returns text language sql immutable as $$
  select 'w' || to_char(p_at at time zone 'utc', 'IYYY-IW');
$$;

-- Settles the previous ISO week once: ranks the nicknamed players' best valid score of that week, per mode, and writes
-- their prize rows. Whoever calls first after Monday 00:00 UTC triggers it; an advisory lock keeps it single.
create or replace function public.settle_week() returns text
language plpgsql security definer set search_path = ''
as $$
declare ws timestamptz := date_trunc('week', now()) - interval '7 days'; we timestamptz := date_trunc('week', now()); wk text; m text;
begin
  wk := public.week_key(ws);
  if exists (select 1 from public.weeks_settled s where s.week = wk) then return wk; end if;
  perform pg_advisory_xact_lock(4242);
  if exists (select 1 from public.weeks_settled s where s.week = wk) then return wk; end if;
  foreach m in array array['defense', 'march'] loop
    insert into public.week_rewards (user_id, week, mode, rank, gems)
    select t.user_id, wk, m, t.pos, public.week_gems(t.pos)
    from (
      select b.user_id, (rank() over (order by b.score desc))::int as pos
      from (select distinct on (r.user_id) r.user_id, r.score
            from public.runs r join public.profiles p on p.id = r.user_id
            where r.valid and r.mode = m and r.finished_at >= ws and r.finished_at < we
            order by r.user_id, r.score desc) b
    ) t where t.pos <= 1000
    on conflict do nothing;
  end loop;
  insert into public.weeks_settled (week) values (wk) on conflict do nothing;
  return wk;
end $$;
revoke execute on function public.settle_week() from public, anon, authenticated;

create or replace function public.get_week_rewards()
returns table (week text, mode text, rank int, gems int, settled text)
language plpgsql security definer set search_path = ''
as $$
declare wk text;
begin
  if auth.uid() is null then raise exception 'not_authenticated'; end if;
  wk := public.settle_week();
  return query select w.week, w.mode, w.rank, w.gems, wk from public.week_rewards w
    where w.user_id = auth.uid() and not w.claimed order by w.week desc, w.mode;
end $$;
revoke execute on function public.get_week_rewards() from public, anon;

create or replace function public.claim_week_reward(p_week text, p_mode text) returns table (gems int)
language plpgsql security definer set search_path = ''
as $$
declare w public.week_rewards;
begin
  if auth.uid() is null then raise exception 'not_authenticated'; end if;
  select * into w from public.week_rewards x where x.user_id = auth.uid() and x.week = p_week and x.mode = p_mode for update;
  if not found then raise exception 'not_found'; end if;
  if w.claimed then raise exception 'claimed'; end if;
  update public.week_rewards set claimed = true where user_id = auth.uid() and week = p_week and mode = p_mode;
  insert into public.wallets (user_id) values (auth.uid()) on conflict do nothing;
  update public.wallets set gems = public.wallets.gems + w.gems, updated_at = now() where user_id = auth.uid();
  return query select x.gems from public.wallets x where x.user_id = auth.uid();
end $$;
revoke execute on function public.claim_week_reward(text, text) from public, anon;

-- ---------- season ----------
create table if not exists public.season_pass (
  user_id uuid not null references auth.users on delete cascade,
  season int not null,
  premium boolean not null default false,
  points int not null default 0,
  free_claimed int not null default 0,
  prem_claimed int not null default 0,
  primary key (user_id, season)
);
alter table public.season_pass enable row level security;
drop policy if exists "le o proprio passe" on public.season_pass;
create policy "le o proprio passe" on public.season_pass for select to authenticated using (user_id = auth.uid());
revoke insert, update, delete on public.season_pass from anon, authenticated;

-- Seasons are 30 days from 2026-10-17 00:00 UTC; 30 tiers of 150 points; the pass costs 120 gems.
create or replace function public.season_start(p_season int) returns timestamptz language sql immutable as $$
  select '2026-10-17 00:00:00+00'::timestamptz + (p_season - 1) * interval '30 days';
$$;
create or replace function public.season_no() returns int language sql stable as $$
  select floor(extract(epoch from (now() - '2026-10-17 00:00:00+00'::timestamptz)) / (30 * 86400))::int + 1;
$$;
create or replace function public.season_tier(p_tier int) returns table (coins_free int, gems_free int, coins_prem int, gems_prem int) language sql immutable as $$
  select 100 + 10 * p_tier, case when p_tier % 5 = 0 then 5 else 0 end, 200 + 20 * p_tier, case when p_tier % 5 = 0 then 10 else 2 end;
$$;

-- Adds season points to the caller (called by finish_run); returns the total.
create or replace function public.season_points(p_add int) returns int
language plpgsql security definer set search_path = ''
as $$
declare s int := public.season_no(); total int;
begin
  insert into public.season_pass (user_id, season) values (auth.uid(), s) on conflict do nothing;
  update public.season_pass set points = public.season_pass.points + p_add where user_id = auth.uid() and season = s returning public.season_pass.points into total;
  return total;
end $$;
revoke execute on function public.season_points(int) from public, anon, authenticated;

create or replace function public.get_season()
returns table (season int, starts_at timestamptz, ends_at timestamptz, points int, tier int, premium boolean, free_claimed int, prem_claimed int, price int)
language plpgsql security definer set search_path = ''
as $$
declare s int := public.season_no(); sp public.season_pass;
begin
  if auth.uid() is null then raise exception 'not_authenticated'; end if;
  select * into sp from public.season_pass x where x.user_id = auth.uid() and x.season = s;
  return query select s, public.season_start(s), public.season_start(s) + interval '30 days', coalesce(sp.points, 0), least(30, coalesce(sp.points, 0) / 150),
    coalesce(sp.premium, false), coalesce(sp.free_claimed, 0), coalesce(sp.prem_claimed, 0), 120;
end $$;
revoke execute on function public.get_season() from public, anon;

create or replace function public.buy_season_pass() returns table (gems int, premium boolean)
language plpgsql security definer set search_path = ''
as $$
declare s int := public.season_no(); sp public.season_pass; have int;
begin
  if auth.uid() is null then raise exception 'not_authenticated'; end if;
  insert into public.season_pass (user_id, season) values (auth.uid(), s) on conflict do nothing;
  select * into sp from public.season_pass x where x.user_id = auth.uid() and x.season = s for update;
  if sp.premium then raise exception 'owned'; end if;
  insert into public.wallets (user_id) values (auth.uid()) on conflict do nothing;
  select w.gems into have from public.wallets w where w.user_id = auth.uid() for update;
  if coalesce(have, 0) < 120 then raise exception 'not_enough_gems'; end if;
  update public.wallets set gems = public.wallets.gems - 120, updated_at = now() where user_id = auth.uid();
  update public.season_pass set premium = true where user_id = auth.uid() and season = s;
  return query select w.gems, true from public.wallets w where w.user_id = auth.uid();
end $$;
revoke execute on function public.buy_season_pass() from public, anon;

-- Claims every reached, unclaimed tier of one track ('free' or 'prem'); returns the wallet and the tier claimed up to.
create or replace function public.claim_season(p_track text) returns table (coins int, gems int, claimed_to int)
language plpgsql security definer set search_path = ''
as $$
declare s int := public.season_no(); sp public.season_pass; tier int; frm int; c int := 0; g int := 0; i int; t record;
begin
  if auth.uid() is null then raise exception 'not_authenticated'; end if;
  select * into sp from public.season_pass x where x.user_id = auth.uid() and x.season = s for update;
  if not found then raise exception 'nothing'; end if;
  tier := least(30, sp.points / 150);
  if p_track = 'prem' then
    if not sp.premium then raise exception 'no_pass'; end if;
    frm := sp.prem_claimed;
  else
    frm := sp.free_claimed;
  end if;
  if tier <= frm then raise exception 'nothing'; end if;
  for i in frm + 1 .. tier loop
    select * into t from public.season_tier(i);
    if p_track = 'prem' then c := c + t.coins_prem; g := g + t.gems_prem; else c := c + t.coins_free; g := g + t.gems_free; end if;
  end loop;
  if p_track = 'prem' then update public.season_pass set prem_claimed = tier where user_id = auth.uid() and season = s;
  else update public.season_pass set free_claimed = tier where user_id = auth.uid() and season = s; end if;
  insert into public.wallets (user_id) values (auth.uid()) on conflict do nothing;
  update public.wallets set coins = public.wallets.coins + c, gems = public.wallets.gems + g, updated_at = now() where user_id = auth.uid();
  return query select w.coins, w.gems, tier from public.wallets w where w.user_id = auth.uid();
end $$;
revoke execute on function public.claim_season(text) from public, anon;

-- ================= Funções =================
drop function if exists public.start_run();
create or replace function public.start_run(p_mode text default 'defense')
returns uuid
language plpgsql security definer set search_path = ''
as $$
declare rid uuid;
begin
  if auth.uid() is null then raise exception 'not_authenticated'; end if;
  delete from public.runs
    where user_id = auth.uid() and finished_at is null and started_at < now() - interval '1 day';
  if (select count(*) from public.runs where user_id = auth.uid() and started_at > now() - interval '10 minutes') >= 30 then
    raise exception 'rate_limited';
  end if;
  insert into public.runs (user_id, mode) values (auth.uid(), case when p_mode = 'march' then 'march' else 'defense' end)
    returning id into rid;
  return rid;
end $$;

-- Defesa: o teto por onda espelha buildWave() do jogo (inimigos comuns + 2 hordas gigantes + brutamontes + chefão +
-- bônus da onda + caixas); pontuação aceita até 2x esse teto. Marcha: p_wave são os metros andados e a estrada nunca
-- passa de 16 m/s, então distância, abates e pontos são limitados pelo tempo da partida; os chefões (um a cada 1000 m,
-- ~140 m antes da marca) valem 900 × mundo, a tropa cheia converte soldados em pontos e o combo multiplica metros e
-- abates por até 3, daí os 12 pontos por metro.
drop function if exists public.finish_run(uuid, int, int, int, int);
drop function if exists public.finish_run(uuid, int, int, int, int, text);
drop function if exists public.finish_run(uuid, int, int, int, int, text, int);
-- finish_run gains p_relics (cages and relics opened) and returns the run's chest and the missions it completed.
drop function if exists public.finish_run(uuid, int, int, int, int, text, int, int);
create or replace function public.finish_run(p_run uuid, p_score int, p_wave int, p_kills int, p_peak int, p_contracts text default null, p_coins int default 0, p_relics int default 0)
returns table (accepted boolean, week_rank int, all_rank int, best int, coins_won int, coins_total int, unlocked text, gems_total int, chest text, chest_coins int, chest_gems int, missions text, season_add int, season_total int)
language plpgsql security definer set search_path = ''
as $$
declare
  r public.runs;
  secs numeric;
  max_score numeric;
  max_kills numeric;
  bosses numeric := 0;
  ncon int := 0;
  ok boolean;
  wal public.wallets;
  won int := 0;
  total int := 0;
  unl text[] := '{}';
  k text;
  tier text := null;
  chest_c int := 0;
  chest_g int := 0;
  done text := null;
  sp_add int := 0;
  sp_total int := null;
  week_start timestamptz := date_trunc('week', now());
begin
  select * into r from public.runs
    where id = p_run and user_id = auth.uid() and finished_at is null
    for update;
  if not found then raise exception 'invalid_run'; end if;

  secs := extract(epoch from now() - r.started_at);
  if r.mode = 'march' then
    bosses := floor((p_wave + 140) / 1000.0);
    -- contracts multiply the score (up to x2.73 with three); the client reports which ones it ran under
    ncon := least(3, coalesce(array_length(string_to_array(coalesce(p_contracts, ''), ','), 1), 0));
    if p_contracts = '' then ncon := 0; end if;
    ok := p_wave between 0 and secs * 16 + 60
      and p_kills between 0 and secs * 30 + 50
      and p_score between 0 and (p_wave * 12 + p_kills * 60 + 450 * bosses * (bosses + 1) + 500) * (1 + 0.65 * ncon)
      and p_peak between 0 and 1000
      and coalesce(p_relics, 0) between 0 and p_wave / 50 + 3;
  else
    select sum(20 * e + 60 * (4 + 1.1 * w) + 50 * w + 1000), sum(e)
      into max_score, max_kills
      from (select w, 18 + 11 * w + 0.85 * w * w + 2 * (30 + 7 * w) + 3 + 1.1 * w as e
            from generate_series(1, greatest(least(p_wave, 500), 1)) w) t;
    ok := p_wave between 1 and 500
      and p_score between 0 and max_score * 2
      and p_kills between 0 and max_kills * 1.5
      and p_peak between 0 and 100000
      and secs >= (p_wave - 1) * 6;
    bosses := floor(p_wave / 5.0);
  end if;

  -- A valid run pays coins: the road's (capped by what the run could have dropped) plus the score's bonus, doubled on
  -- the day's first three runs, then limited to 5000 a day.
  if ok then
    select * into wal from public.wallets where user_id = auth.uid() for update;
    if not found then insert into public.wallets (user_id) values (auth.uid()) returning * into wal; end if;
    if wal.day <> current_date then wal.runs_today := 0; wal.earned_today := 0; wal.chests_today := 0; end if;
    won := greatest(20, p_score / 200) + least(greatest(coalesce(p_coins, 0), 0), 2 * (p_kills + 150 * bosses::int + 50)); -- x2: the Thief's share
    if wal.runs_today < 3 then won := won * 2; else won := least(won, greatest(0, 5000 - wal.earned_today)); end if;
    -- The run's chest: the tier comes from how far it went, the contents are rolled here, five chests a day at most.
    -- bronze 20-50 coins (4%: 1 gem), silver 60-150 (12%: 1-3 gems), gold 180-400 (30%: 3-8 gems).
    if r.mode = 'march' then
      tier := case when p_wave >= 6000 then 'gold' when p_wave >= 2500 then 'silver' when p_wave >= 500 then 'bronze' end;
    else
      tier := case when p_wave >= 15 then 'gold' when p_wave >= 8 then 'silver' when p_wave >= 3 then 'bronze' end;
    end if;
    if tier is not null and wal.chests_today < 5 then
      chest_c := case tier when 'gold' then 180 + floor(random() * 221)::int when 'silver' then 60 + floor(random() * 91)::int else 20 + floor(random() * 31)::int end;
      chest_g := case when tier = 'gold' and random() < 0.30 then 3 + floor(random() * 6)::int
                      when tier = 'silver' and random() < 0.12 then 1 + floor(random() * 3)::int
                      when tier = 'bronze' and random() < 0.04 then 1 else 0 end;
    else
      tier := null;
    end if;
    update public.wallets
      set coins = coins + won + chest_c, gems = gems + chest_g, earned_today = wal.earned_today + won, runs_today = wal.runs_today + 1,
          chests_today = wal.chests_today + (case when tier is null then 0 else 1 end), day = current_date, updated_at = now()
      where user_id = auth.uid() returning coins into total;
    -- achievements this run earns (each pays its gems once)
    if r.mode = 'march' then
      foreach k in array array['first_march', 'boss1', 'km2', 'km5', 'km8', 'km12', 'score100k', 'score500k', 'kills1k', 'contracts3'] loop
        if (k = 'first_march' and p_wave >= 200) or (k = 'boss1' and p_wave >= 1000) or (k = 'km2' and p_wave >= 2000) or (k = 'km5' and p_wave >= 5000)
           or (k = 'km8' and p_wave >= 8000) or (k = 'km12' and p_wave >= 12000) or (k = 'score100k' and p_score >= 100000) or (k = 'score500k' and p_score >= 500000)
           or (k = 'kills1k' and p_kills >= 1000) or (k = 'contracts3' and ncon >= 3 and p_wave >= 2000) then
          if public.grant_achievement(k) > 0 then unl := unl || k; end if;
        end if;
      end loop;
    else
      if p_wave >= 10 and public.grant_achievement('defense10') > 0 then unl := unl || 'defense10'; end if;
      if p_wave >= 20 and public.grant_achievement('defense20') > 0 then unl := unl || 'defense20'; end if;
    end if;
    -- the missions this run advances, then the season points
    done := public.mission_progress(r.mode, p_wave, p_wave, p_kills, bosses::int, greatest(coalesce(p_coins, 0), 0), p_score, p_peak, ncon, coalesce(p_relics, 0));
    sp_add := least(60, 10 + (case when r.mode = 'march' then p_wave / 100 else 2 * p_wave end))
      + 25 * coalesce(array_length(string_to_array(done, ','), 1), 0);
    sp_total := public.season_points(sp_add);
  end if;

  update public.runs
    set finished_at = now(), score = p_score, wave = p_wave, kills = p_kills, peak = p_peak, valid = ok, contracts = nullif(p_contracts, '')
    where id = p_run;

  if not ok then
    return query select false, null::int, null::int, null::int, 0, (select w.coins from public.wallets w where w.user_id = auth.uid()), null::text, (select w.gems from public.wallets w where w.user_id = auth.uid()), null::text, 0, 0, null::text, 0, null::int;
    return;
  end if;

  -- Position among each nicknamed player's best, same mode (the player counts even without a nickname).
  return query
    with mine as (
      select max(x.score) as all_best,
             max(x.score) filter (where x.finished_at >= week_start) as week_best
      from public.runs x where x.user_id = auth.uid() and x.valid and x.mode = r.mode
    ), others as (
      select x.user_id,
             max(x.score) as all_best,
             max(x.score) filter (where x.finished_at >= week_start) as week_best
      from public.runs x
      join public.profiles p on p.id = x.user_id
      where x.valid and x.mode = r.mode and x.user_id <> auth.uid()
      group by x.user_id
    )
    select true,
           (select count(*)::int + 1 from others o where o.week_best > m.week_best),
           (select count(*)::int + 1 from others o where o.all_best > m.all_best),
           m.all_best, won, total, nullif(array_to_string(unl, ','), ''), (select w.gems from public.wallets w where w.user_id = auth.uid()),
           tier, chest_c, chest_g, done, sp_add, sp_total
    from mine m;
end $$;
revoke execute on function public.finish_run(uuid, int, int, int, int, text, int, int) from public, anon, authenticated;
grant execute on function public.finish_run(uuid, int, int, int, int, text, int, int) to authenticated;

-- p_period: 'week' (semana atual, UTC, começando na segunda) ou 'all'. p_mode: 'defense' ou 'march'.
-- Devolve o top N e, se o jogador estiver fora dele, a linha dele no fim.
drop function if exists public.get_leaderboard(text, int);
drop function if exists public.get_leaderboard(text, int, text);
create or replace function public.get_leaderboard(p_period text default 'week', p_limit int default 50, p_mode text default 'defense')
returns table (pos int, nickname text, score int, wave int, is_me boolean, contracts text, badge text, pass boolean)
language sql stable security definer set search_path = ''
as $$
  with best as (
    select distinct on (r.user_id) r.user_id, r.score, r.wave, r.finished_at, r.contracts
    from public.runs r
    where r.valid and r.mode = p_mode and (p_period = 'all' or r.finished_at >= date_trunc('week', now()))
    order by r.user_id, r.score desc, r.finished_at
  ), ranked as (
    select (rank() over (order by b.score desc))::int as pos, p.nickname, b.score, b.wave, b.finished_at, b.contracts,
           b.user_id is not distinct from auth.uid() as is_me,
           (select case when w.rank = 1 then 'top1' when w.rank <= 10 then 'top10' end from public.week_rewards w
              where w.user_id = b.user_id and w.mode = p_mode and w.week = public.week_key(date_trunc('week', now()) - interval '7 days')) as badge,
           exists (select 1 from public.season_pass sp where sp.user_id = b.user_id and sp.season = public.season_no() and sp.premium) as pass
    from best b join public.profiles p on p.id = b.user_id
  )
  select pos, nickname, score, wave, is_me, contracts, badge, pass from ranked
  where pos <= least(p_limit, 100) or is_me
  order by pos, finished_at
  limit least(p_limit, 100) + 1;
$$;
revoke execute on function public.get_leaderboard(text, int, text) from public, anon, authenticated;
grant execute on function public.get_leaderboard(text, int, text) to anon, authenticated;

revoke execute on function public.start_run(text) from public, anon, authenticated;
revoke execute on function public.get_wallet() from public, anon, authenticated;
revoke execute on function public.buy_quartel(text) from public, anon, authenticated;
revoke execute on function public.refund_quartel() from public, anon, authenticated;
revoke execute on function public.buy_hero(text, text) from public, anon, authenticated;
revoke execute on function public.level_hero(text) from public, anon, authenticated;
revoke execute on function public.grant_achievement(text) from public, anon, authenticated;
grant execute on function public.start_run(text) to authenticated;
grant execute on function public.get_wallet() to authenticated;
grant execute on function public.buy_quartel(text) to authenticated;
grant execute on function public.refund_quartel() to authenticated;
grant execute on function public.buy_hero(text, text) to authenticated;
grant execute on function public.level_hero(text) to authenticated;
-- the economy's internal functions are owner-only; the player-facing RPCs need a signed-in player
revoke execute on function public.mission_progress(text, int, int, int, int, int, int, int, int, int) from public, anon, authenticated;
revoke execute on function public.season_points(int) from public, anon, authenticated;
revoke execute on function public.settle_week() from public, anon, authenticated;
grant execute on function public.get_missions() to authenticated;
grant execute on function public.claim_mission(text, text) to authenticated;
grant execute on function public.get_week_rewards() to authenticated;
grant execute on function public.claim_week_reward(text, text) to authenticated;
grant execute on function public.get_season() to authenticated;
grant execute on function public.buy_season_pass() to authenticated;
grant execute on function public.claim_season(text) to authenticated;
