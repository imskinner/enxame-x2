# Enxame ×2

Jogo de navegador em 3D (Three.js): seu canhão dispara uma tropa, os portões multiplicam os soldados e você precisa segurar a horda antes que ela chegue ao muro. A cada 5 ondas vem um chefão elemental (gelo, fogo, lava, tempestade, água, veneno, zumbi e buraco negro) e o mapa vai virando o mundo dele.

**Jogar:** https://imskinner.github.io/enxame-x2/

## Controles

- Mover: mouse, arrastar o dedo, `A`/`D` ou `←`/`→`
- Ultimate: `Espaço` ou `Q`
- Pausa: `P` · Som: `M`

## Rodar localmente

É um único `index.html` sem build. Sirva a pasta com qualquer servidor estático:

```sh
python3 -m http.server 8000
# abra http://localhost:8000
```

## Ranking e login (Supabase)

Opcional: sem chave configurada o jogo roda 100% offline. Para ligar:

1. No SQL Editor do projeto, rode [`supabase/schema.sql`](supabase/schema.sql).
2. Em **Authentication → Sign In / Providers**: ative **Allow anonymous sign-ins** e **Allow manual linking**. Para "Entrar com Google", configure o provider Google.
3. Em **Authentication → URL Configuration**: Site URL `https://imskinner.github.io/enxame-x2/`; Redirect URLs com ela e `http://localhost:8000/`.
4. Cole a chave publishable em `SUPABASE_KEY` no `index.html`.

Quem joga entra automaticamente como convidado; ao fim da partida escolhe um apelido. Vincular Google ou e-mail transforma o convidado em conta permanente sem perder os pontos. A pontuação só é gravada pelas funções `start_run`/`finish_run`, que medem o tempo no servidor e recusam valores impossíveis para a onda. Partidas com atalhos de teste na URL não contam.

Atalhos de teste pela URL: `#w13t20` pula para a onda 13 e simula 20 s; flags `u` (ultimate), `c` (câmera próxima), `b` (invoca chefão), `k` (mata o chefão).
