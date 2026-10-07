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
  score int, wave int, kills int, peak int,
  valid boolean not null default false
);
create index if not exists runs_user_started on public.runs (user_id, started_at);
create index if not exists runs_valid_finished on public.runs (finished_at, score desc) where valid;

-- Sem políticas: ninguém lê ou grava a tabela direto, só pelas funções abaixo.
alter table public.runs enable row level security;
revoke all on public.runs from anon, authenticated;

-- ================= Funções =================
create or replace function public.start_run()
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
  insert into public.runs (user_id) values (auth.uid()) returning id into rid;
  return rid;
end $$;

-- Teto por onda espelha buildWave() do jogo: inimigos comuns + 2 hordas gigantes
-- + brutamontes + chefão + bônus da onda + caixas. Pontuação aceita até 2× esse teto.
create or replace function public.finish_run(p_run uuid, p_score int, p_wave int, p_kills int, p_peak int)
returns table (accepted boolean, week_rank int, all_rank int, best int)
language plpgsql security definer set search_path = ''
as $$
declare
  r public.runs;
  secs numeric;
  max_score numeric;
  max_kills numeric;
  ok boolean;
  week_start timestamptz := date_trunc('week', now());
begin
  select * into r from public.runs
    where id = p_run and user_id = auth.uid() and finished_at is null
    for update;
  if not found then raise exception 'invalid_run'; end if;

  secs := extract(epoch from now() - r.started_at);
  select sum(20 * e + 60 * (4 + 1.1 * w) + 50 * w + 1000), sum(e)
    into max_score, max_kills
    from (select w, 18 + 11 * w + 0.85 * w * w + 2 * (30 + 7 * w) + 3 + 1.1 * w as e
          from generate_series(1, greatest(least(p_wave, 500), 1)) w) t;

  ok := p_wave between 1 and 500
    and p_score between 0 and max_score * 2
    and p_kills between 0 and max_kills * 1.5
    and p_peak between 0 and 100000
    and secs >= (p_wave - 1) * 6;

  update public.runs
    set finished_at = now(), score = p_score, wave = p_wave, kills = p_kills, peak = p_peak, valid = ok
    where id = p_run;

  if not ok then
    return query select false, null::int, null::int, null::int;
    return;
  end if;

  -- Posição entre os melhores de cada jogador com apelido (o próprio jogador conta mesmo sem apelido).
  return query
    with mine as (
      select max(x.score) as all_best,
             max(x.score) filter (where x.finished_at >= week_start) as week_best
      from public.runs x where x.user_id = auth.uid() and x.valid
    ), others as (
      select x.user_id,
             max(x.score) as all_best,
             max(x.score) filter (where x.finished_at >= week_start) as week_best
      from public.runs x
      join public.profiles p on p.id = x.user_id
      where x.valid and x.user_id <> auth.uid()
      group by x.user_id
    )
    select true,
           (select count(*)::int + 1 from others o where o.week_best > m.week_best),
           (select count(*)::int + 1 from others o where o.all_best > m.all_best),
           m.all_best
    from mine m;
end $$;

-- p_period: 'week' (semana atual, UTC, começando na segunda) ou 'all'.
-- Devolve o top N e, se o jogador estiver fora dele, a linha dele no fim.
create or replace function public.get_leaderboard(p_period text default 'week', p_limit int default 50)
returns table (pos int, nickname text, score int, wave int, is_me boolean)
language sql stable security definer set search_path = ''
as $$
  with best as (
    select distinct on (r.user_id) r.user_id, r.score, r.wave, r.finished_at
    from public.runs r
    where r.valid and (p_period = 'all' or r.finished_at >= date_trunc('week', now()))
    order by r.user_id, r.score desc, r.finished_at
  ), ranked as (
    select (rank() over (order by b.score desc))::int as pos, p.nickname, b.score, b.wave, b.finished_at,
           b.user_id is not distinct from auth.uid() as is_me
    from best b join public.profiles p on p.id = b.user_id
  )
  select pos, nickname, score, wave, is_me from ranked
  where pos <= least(p_limit, 100) or is_me
  order by pos, finished_at
  limit least(p_limit, 100) + 1;
$$;

revoke execute on function public.start_run() from public, anon, authenticated;
revoke execute on function public.finish_run(uuid, int, int, int, int) from public, anon, authenticated;
revoke execute on function public.get_leaderboard(text, int) from public, anon, authenticated;
grant execute on function public.start_run() to authenticated;
grant execute on function public.finish_run(uuid, int, int, int, int) to authenticated;
grant execute on function public.get_leaderboard(text, int) to anon, authenticated;
