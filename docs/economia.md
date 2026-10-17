# Economia e progressão do Enxame ×2

Documento de design, 2026-10-10. Base: pesquisa sobre Archero, Survivor.io, Count Masters, Squad Busters, Brawl Stars, Vampire Survivors, Rogue Legacy, Dead Cells e Hades, mais a literatura de economia e psicologia de free-to-play (referências no fim).

## Decisões fixas

- **Sem energia.** Jogar nunca é bloqueado por tempo. O aperto é positivo: as três primeiras runs do dia rendem moedas em dobro.
- **Sem "continuar".** Morreu, acabou a run. O ranking só é justo se toda pontuação vem de uma vida.
- **Nada pago altera a pontuação.** Tudo que muda o placar (atributos, heróis em nível, contratos) se compra só com moedas ganhas jogando.
- **Preços em reais, com Pix** (Stripe Checkout).
- **Aleatoriedade só nas recompensas gratuitas.** O que é pago é determinístico: você compra o que vê.

## Princípio

A habilidade decide a run; a meta decide até onde a habilidade alcança; o dinheiro decide quão rápido você amplia as opções, nunca o teto.

O que a pesquisa diz e que sustenta isso:

1. Moeda dupla é o padrão (ouro para progredir, gema para acelerar). O risco é o fim de jogo: quando a progressão para de render, a receita morre junto (crítica ao Archero).
2. Crowd runners rasos morrem de rasos: os jogadores pedem profundidade e reclamam que, com os números escalando, a habilidade deixa de decidir.
3. Meta-progressão por poder puro deixa o jogo mais fácil com o tempo (Rogue Legacy). Prefira unlocks que ampliam opções, poder limitado com custo crescente e reembolso, e dificuldade que escala junto (Vampire Survivors, Hades).
4. Aleatoriedade engaja, mas não deve ser vendida: a Supercell tirou as caixas do Brawl Stars, perdeu engajamento e voltou com recompensas aleatórias que só se ganham jogando.
5. Nada de poder comprado em modo ranqueado, experiência gratuita completa, caminho gratuito para cosméticos, probabilidades divulgadas.
6. Reforço de razão variável (baús) sustenta o hábito; flow pede desafio na altura da habilidade; autodeterminação pede autonomia (builds, heróis, contratos), competência (padrões legíveis) e pertencimento (ranking, temporadas).
7. Incentivos: a jogada divertida tem que ser a ótima (sem farm degenerado), o ranking é um torneio (modificadores transparentes) e o caminho gratuito tem que ser crível.

## Moedas e diamantes

| | Moedas | Diamantes |
|---|---|---|
| Fontes | caem na pista (abates, portões, chefão); bônus no fim da run proporcional à pontuação; missões diárias; baús | conquistas (primeira vitória sobre cada chefão, marcos de distância); missões semanais; ranking semanal por faixa; passe gratuito; pacotes pagos |
| Sumidouros | Quartel; heróis (caminho lento); skins baratas | heróis (caminho rápido); skins e rastros; passe premium; cor do nome no ranking; slot extra de contrato |
| Aperto | retorno decrescente: 3 primeiras runs do dia em dobro, depois normal | escassez: 20 a 40 por semana jogando; pacotes de 100 a 1.500 |

Moedas por run (calculadas pelo servidor em `finish_run`): `pontuação / 100`, com piso de 20 e teto diário de 5.000 fora das três runs em dobro. Moedas caídas na pista são contadas no cliente e validadas contra abates e metros, como a pontuação.

## Quartel (meta, só moedas)

Melhorias permanentes com preço que cresce 15% por nível e reembolso total a qualquer hora.

| Melhoria | Níveis | Efeito por nível |
|---|---|---|
| Recrutas | 10 | +2 soldados iniciais |
| Alojamento | 6 | +10 no teto da tropa |
| Arsenal | 6 | +10% no teto de cadência e dano |
| Disciplina | 4 | FILA +0,3 s de duração |
| Cornetas | 4 | FILA −0,5 s de recarga |
| Bateria | 4 | ultimate começa com +10% |
| Alquimia | 1 | terceiro slot de elemento |

É aqui que a meta vira "necessária eventualmente": o segundo ciclo de mundos é balanceado para um Quartel maduro mais um herói, não para uma conta nova.

## Heróis

Uma unidade maior na tropa, um por run, com passiva e ativa. São estilos, não degraus. Níveis de herói (1 a 5) só com moedas; desbloqueio por moedas (caminho longo) ou diamantes (caminho curto).

| Herói | Passiva | Ativa (junto com a FILA) |
|---|---|---|
| Muralha | absorve o primeiro golpe de cada padrão num raio de 3 m | escudo de 2 s para a coluna |
| Arqueira | +20% de alcance | rajada perfurante |
| Engenheira | relíquia libertada solta uma torre por 10 s | torre instantânea na frente |
| Médica | recupera 5% dos caídos a cada portão | cura em área |
| Batedor | FILA +1 s e −2 s de recarga | dash lateral |
| Alquimista | guarda três elementos | troca a ordem dos elementos |
| Ladrão | +50% de moedas na run | ímã de moedas |
| Bardo | cada soldado perdido tira 5 do combo em vez de 10 | +1 nível de combo |

Os primeiros três a implementar: Muralha, Arqueira, Ladrão (um defensivo, um ofensivo, um econômico).

## Contratos (habilidade vira pontos)

Modificadores opcionais escolhidos antes da run, até três por vez, cada um com multiplicador no placar:

| Contrato | Efeito | Placar |
|---|---|---|
| Sem FILA | a habilidade some | ×1,4 |
| Sem reforços | o portal de reforços não aparece | ×1,2 |
| Fúria desde o início | chefão nasce em fúria | ×1,3 |
| Brechas estreitas | muros e padrões com brechas 30% menores | ×1,25 |
| Horda dobrada | o dobro de inimigos por trecho | ×1,2 |
| Tropa enxuta | teto da tropa pela metade | ×1,5 |

É o "Heat" de Hades: profundidade no ranking sem vender poder. O ranking mostra os contratos da run.

## Baús, missões, temporada e eventos

- **Baú de fim de run (feito):** o servidor sorteia em `finish_run`, até cinco por dia. Bronze (500 m ou onda 3): 20 a 50 moedas, 4% de 1 diamante. Prata (2.500 m ou onda 8): 60 a 150 moedas, 12% de 1 a 3 diamantes. Ouro (6.000 m ou onda 15): 180 a 400 moedas, 30% de 3 a 8 diamantes. Nunca comprável; as probabilidades ficam na tela Missões. Fragmentos de skin entram quando houver skins.
- **Missões (feito):** 3 diárias (moedas, 60 a 100) e 3 semanais (diamantes, 10 a 20), sorteadas por um hash do dia/semana UTC, as mesmas para todo mundo. O progresso é somado (ou o melhor guardado) em `mission_progress`, chamada por `finish_run` só em partidas válidas; a recompensa é pega em `claim_mission`. Alvos e prêmios vivem em `mission_def` no servidor; o cliente só tem os textos.
- **Temporada de 30 dias (feito):** janelas de 30 dias a partir de 2026-10-17 UTC (`season_no`). Pontos por partida válida: 10 mais 1 por 100 m na marcha ou 2 por onda na defesa (até 60), e 25 por missão concluída, creditados por `finish_run` em `season_points`. 30 níveis de 150 pontos (`season_tier`): trilha grátis 100+10n moedas e 5 diamantes a cada cinco níveis; trilha premium 200+20n moedas, 2 diamantes por nível e 10 a cada cinco (138 diamantes no total). Passe premium a 120 diamantes (`buy_season_pass`, por Pix via Stripe depois), que também dá a estrela ✦ no ranking. `claim_season` paga todos os níveis alcançados de uma trilha. Um jogador diário (3 partidas e as missões) fecha o passe em uns 25 dias. O tema e o herói de estreia entram quando houver um novo por temporada.
- **Eventos de fim de semana:** moedas em dobro, mundo em fúria, chefão convidado.
- **Ranking semanal (feito):** na primeira chamada depois de segunda 00:00 UTC o servidor liquida a semana anterior (`settle_week`, uma vez, com trava): melhor partida válida de cada jogador com apelido, por modo, e grava os prêmios (#1 25, top 10 12, top 100 5, top 1000 2 diamantes) para pegar na tela de ranking (`claim_week_reward`). `get_leaderboard` marca o top 10 da semana anterior (cor do nome, coroa no #1) e quem tem o passe (✦).

## Loja e pagamento

| Item | Preço |
|---|---|
| 100 diamantes | R$ 9,90 |
| 300 diamantes | R$ 24,90 |
| 700 diamantes | R$ 49,90 |
| 1.500 diamantes | R$ 99,90 |
| Pacote de início (uma vez: 150 diamantes + skin) | R$ 4,90 |
| Passe da temporada | R$ 19,90 |
| Skins e heróis | preço fixo em diamantes |

Arquitetura: Stripe Checkout com Pix e cartão; o cliente chama uma Edge Function do Supabase que cria a sessão (chave secreta nunca no navegador); o webhook `checkout.session.completed` credita os diamantes numa função Postgres, idempotente por ID de sessão (tabela de créditos com restrição única); carteira com RLS (o jogador lê, só o servidor escreve); todo gasto via RPC com tabela de preços no servidor. Ofertas casadas com o ciclo de vida: pacote de início no dia 1, primeira oferta de passe no dia 3, oferta de herói no dia 14.

## O que diamantes nunca compram

Atributos, níveis de herói, continuar após morrer, itens durante a run, vantagem em contratos, posição no ranking.

## Anti-farm e anti-cheat

- `finish_run` continua validando pontuação, metros e abates pelo tempo da partida; as moedas derivam dessa validação.
- Teto diário de moedas; retorno decrescente por run no mesmo dia.
- Baús e missões só são concedidos pelo servidor a partir de runs válidas.
- Compras só pelo webhook; nunca pela tela de sucesso.

## Métricas para acompanhar

D1/D7/D30, runs por dia por jogador, moedas ganhas e gastas por dia (fonte × sumidouro), conversão para pagante, ARPDAU, distribuição de contratos usados no top 100 (se o top for só Quartel cheio sem contrato, a meta está mandando mais que a habilidade).

## Roteiro

1. Curva de habilidade (2 PRs): padrões de chefão com zona segura e dano sem teto, formação compacta, armadilhas com caminho livre, contratos.
2. Base da economia (1 PR): moedas na pista e no fim da run, carteira no servidor, Quartel, tela de fim de run.
3. Heróis (2 PRs): Muralha, Arqueira, Ladrão; seleção; desbloqueio por moedas ou diamantes; conquistas que dão diamantes.
4. Temas novos de dois em dois (feito: dezoito mundos), missões e baús (feito), ranking semanal com prêmios e temporada (feito).
5. Loja com Stripe por último, quando houver o que vender.

## Referências

- Deconstructor of Fun, Archero: https://www.deconstructoroffun.com/blog/2019/8/9/why-archero-banked-25m-but-leaves-25m-hanging-hlx9n
- Game Developer, Finding the Fun: Archero monetization: https://www.gamedeveloper.com/design/finding-the-fun-archero-part-3---monetization
- Naavik, Survivor.io: https://naavik.co/deep-dives/survivorio-archeros-footsteps/
- mobilegamer.biz, retenção do Survivor.io: https://mobilegamer.biz/two-months-in-survivor-io-passes-75m-from-37m-downloads/
- Count Masters, análises e avaliações: https://thecasualappgamer.com/count-masters-crowd-runner-3d/
- Vampire Survivors, o molho secreto: https://jboger.substack.com/p/the-secret-sauce-of-vampire-survivors
- bugnet, meta-progressão em roguelites: https://bugnet.io/blog/how-to-design-a-roguelite-meta-progression
- Game Maker's Toolkit, Roguelikes, Persistency and Progression: https://www.youtube.com/watch?v=G9FB5R4wVno
- Deconstructor of Fun, por que tirar as caixas do Brawl Stars falhou: https://www.deconstructoroffun.com/blog/why-removing-loot-boxes-in-brawlstars-failed
- Liquid & Grit, economia do Squad Busters: https://www.liquidandgrit.com/?p=14281
- Udonis, economia equilibrada: https://www.blog.udonis.co/mobile-marketing/mobile-games/balanced-mobile-game-economy
- Adrian Crook, recursos premium e gratuitos: https://adriancrook.com/?p=8177
- Wayline, microtransações éticas: https://www.wayline.io/blog/ethical-microtransactions-monetization-player-trust-free-to-play-games
- Game Developer, classificando pay-to-win: https://www.gamedeveloper.com/business/classifying-pay-to-win-design-in-today-s-market
- Supabase, webhooks do Stripe em Edge Functions: https://supabase.com/docs/guides/functions/examples/stripe-webhooks.md
