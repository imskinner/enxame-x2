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

Atalhos de teste pela URL: `#w13t20` pula para a onda 13 e simula 20 s; flags `u` (ultimate), `c` (câmera próxima), `b` (invoca chefão), `k` (mata o chefão).
