# Enxame ×2

Jogo de navegador em 3D (Three.js): seu canhão dispara uma tropa, os portões multiplicam os soldados e você precisa segurar a horda antes que ela chegue ao muro. A cada 5 ondas vem um chefão elemental (gelo, fogo, lava, tempestade, água, veneno, zumbi e buraco negro) e o mapa vai virando o mundo dele.

**Jogar:** https://imskinner.github.io/enxame-x2/

## Modos

- **Defesa:** o canhão dispara a tropa, os portões a multiplicam e você segura a horda antes do muro.
- **Marcha:** a tropa corre por uma estrada sem fim atirando para a frente. Portões dourados melhoram a arma (cadência, dano, alcance) e atirar neles aumenta o número: um -8% pode virar +4%. Portões verdes-água multiplicam a tropa; matar a horda recruta soldados novos, jaulas guardam reféns e relíquias acorrentadas dão um bônus (rajada, tiro triplo, dano, ultimate) quando você as liberta à bala. A cada 1000 m um chefão para a estrada; ao vencê-lo, um portal se abre e atravessá-lo dá à tropa o elemento dele (gelo congela, fogo queima, lava explode, raio salta, água atravessa, veneno deixa poças, zumbi recruta em dobro, buraco negro persegue) e leva ao mundo do próximo chefão. A tropa guarda dois elementos; no terceiro, você escolhe qual trocar. Ranking separado.

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

## Modelos 3D (Blender)

Árvores, pedras, castelos, objetos da pista (lanternas, cercas, barris, estandartes, colunas dos portões), o canhão, os personagens e os ogros são gerados por script em `tools/blender/` e exportados para `assets/*.glb`. Sem esses arquivos o jogo usa as formas simples feitas em código. Para regenerar:

```sh
blender --background --factory-startup --python tools/blender/flora.py
blender --background --factory-startup --python tools/blender/castle.py
blender --background --factory-startup --python tools/blender/props.py
blender --background --factory-startup --python tools/blender/characters.py
blender --background --factory-startup --python tools/blender/ogre.py
# prévia em PNG: blender --background --factory-startup --python tools/blender/preview.py -- assets/flora.glb previa.png
```

## Ranking e login (Supabase)

Opcional: sem chave configurada o jogo roda 100% offline. Para ligar:

1. No SQL Editor do projeto, rode [`supabase/schema.sql`](supabase/schema.sql).
2. Em **Authentication → Sign In / Providers**: ative **Allow anonymous sign-ins** e **Allow manual linking**. Para "Entrar com Google", configure o provider Google.
3. Em **Authentication → URL Configuration**: Site URL `https://imskinner.github.io/enxame-x2/`; Redirect URLs com ela e `http://localhost:8000/`.
4. Cole a chave publishable em `SUPABASE_KEY` no `index.html`.

Quem joga entra automaticamente como convidado; ao fim da partida escolhe um apelido. Vincular Google ou e-mail transforma o convidado em conta permanente sem perder os pontos. A pontuação só é gravada pelas funções `start_run`/`finish_run`, que medem o tempo no servidor e recusam valores impossíveis para a onda. Partidas com atalhos de teste na URL não contam.

Atalhos de teste pela URL: `#march` inicia a marcha; `#march850` começa aos 850 m com uma tropa já crescida (`#march2850` também traz os elementos dos chefões anteriores); acrescente `t60` (`#march0t60`) para jogar 60 s instantâneos com um robô que escolhe portões, e veja o resumo no console.

Na defesa: `#w13t20` pula para a onda 13 e simula 20 s; flags `u` (ultimate), `c` (câmera próxima), `b` (invoca chefão), `k` (mata o chefão).
