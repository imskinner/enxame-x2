# Enxame ×2

Jogo de navegador em 3D (Three.js): seu canhão dispara uma tropa, os portões multiplicam os soldados e você precisa segurar a horda antes que ela chegue ao muro. A cada 5 ondas vem um chefão elemental (gelo, fogo, lava, tempestade, água, veneno, zumbi e buraco negro) e o mapa vai virando o mundo dele.

**Jogar:** https://imskinner.github.io/enxame-x2/

## Modos

- **Defesa:** o canhão dispara a tropa, os portões a multiplicam e você segura a horda antes do muro.
- **Marcha:** a tropa corre por uma estrada sem fim atirando para a frente. Portões dourados melhoram a arma (cadência, dano, alcance) e atirar neles aumenta o número: um -8% pode virar +4%. Portões verdes-água multiplicam a tropa e as jaulas guardam reféns (os únicos soldados novos); matar a horda carrega o ultimate, e relíquias acorrentadas dão um bônus (rajada, tiro triplo, dano, ultimate) quando você as liberta à bala. O teto da tropa começa em 150 e sobe 25 por mundo até 300; com a tropa cheia, cada soldado que não cabe vira 10 pontos. Abates sem perder soldado sobem um combo de até ×3 nos metros e nos abates; cada soldado perdido o derruba. Na marcha o ultimate carrega mais ou menos uma vez por mundo e o chefão devolve metade ao cair: gaste na corrida ou guarde para ele. A partir do segundo mundo um par de portões pode ser ruim contra ruim (atire no dourado para virá-lo) e do terceiro em diante o portão solitário balança. A cada 1000 m um chefão surge logo além do alcance da tropa, a estrada para e ele vem andando num ritmo constante; começa a atacar assim que a tropa consegue acertá-lo. Cada golpe é um padrão marcado no chão com uma brecha segura, alternando um que a tropa inteira desvia de lado e um que só a FILA atravessa: quem vai para a brecha não perde ninguém, quem fica perde tudo que estiver dentro. A cada volta completa pelos oito mundos o aviso encurta, as brechas estreitam e o ritmo acelera, enquanto a vida do chefão cresce pouco. Se ele chega à frente da tropa entra em fúria (golpes 1,5× mais rápidos, subindo um degrau a cada 20 s até 3×), e uma relíquia acorrentada cai na pista diante da tropa (rajada ou tiro triplo pegos ali duram 12 s). A habilidade **FILA** afunila a tropa por 2 s (3 s com chefão na pista; recarga de 6 s, ou 3,5 s durante o chefão): serve para escolher o portão, passar pela brecha dos muros, que estreita com a distância (a coluna afina para caber), desviar dos obstáculos e concentrar o fogo no chefão. Derrubá-lo vale 600 pontos por mundo, mais 300 por mundo se cair a mais de 20 m da tropa, e um quinto do teto em reféns se junta à tropa ao atravessar o portal do elemento. Atravessá-lo dá à tropa o elemento dele (gelo congela, fogo queima chefões e caixas, lava explode, raio salta, água atravessa, veneno deixa poças, zumbi ergue os mortos contra a horda, buraco negro persegue) e leva ao mundo do próximo chefão. Cada mundo também tem seu obstáculo na estrada, sempre com aviso: pista escorregadia no gelo, poças de fogo, fendas de lava que explodem em ciclos, raios marcados por um círculo, correntezas que arrastam a tropa, nuvens de gás, covas de onde saem mortos e buracos negros que puxam. Ao lado dele abre um portal de REFORÇOS, que enche a tropa até o teto em vez de dar o poder. A tropa guarda dois elementos; no terceiro, são dois portais de troca mais o de reforços. O portal escolhido acende e a tropa entra em fila nele. As armadilhas da estrada, como os golpes dos chefões, matam quem tocam, mas sempre deixam um caminho ou uma pausa para passar. A horda, as jaulas, as relíquias e os chefões deixam **moedas** na pista; no fim da run o servidor paga essas moedas mais um bônus da pontuação (em dobro nas três primeiras runs do dia) e elas compram melhorias permanentes no **Quartel** (recrutas, alojamento, arsenal, disciplina, cornetas, bateria, alquimia), com preço que sobe 15% por nível e reembolso total. Na tela **Heróis** se desbloqueia, com moedas ou diamantes, uma unidade maior para levar na marcha (Muralha, cujo escudo salva quem está perto; Arqueira, que vê mais longe; Ladrão, que rende mais moedas), cada uma com uma ativa que dispara junto com a FILA e níveis pagos só com moedas. As **conquistas** (primeiro chefão, marcos de distância e de pontos, três contratos, ondas da defesa) são conferidas pelo servidor ao fim da partida e pagam diamantes uma vez. Antes de marchar dá para assinar até três **contratos** (sem FILA, sem reforços, fúria desde o início, brechas estreitas, horda dobrada, tropa enxuta), cada um multiplicando a pontuação; o ranking mostra o multiplicador. Ranking separado.

## Controles

- Mover: mouse, arrastar o dedo, `A`/`D` ou `←`/`→`
- Ultimate: `Espaço` ou `Q`
- FILA (Marcha): `S`, `↑`, clique do mouse ou o botão (também `W` e `Shift`)
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

`#fps` mostra no alto da tela a taxa de quadros, o pior quadro, as chamadas de desenho e o tamanho das multidões: serve para medir o desempenho num celular sem devtools.
