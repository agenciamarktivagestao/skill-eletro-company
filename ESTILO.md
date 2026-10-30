# Estilo de edição: Eletro Company

Padrão montado em 27/10/2026 a partir do **manual de marca** (`REFERENCIAS/MANUAL DE MARCA - Eletro Company.pdf`), do **logo** (`REFERENCIAS/logo Eletro Company.png`), da **referência de legenda** (`REFERENCIAS/referencia_legenda.mp4`) e de um **vídeo antigo** da Eletro já editado (`REFERENCIAS/video_base_IMG_4879.MOV`, que tem legendas queimadas, então só serve de referência de formato, tom e CTA). O resumo visual fica em `REFERENCIAS/padrao_eletro.jpg`. Registre aqui tudo o que o cliente aprovar ou recusar.

> **Padrão definitivo** (aprovado pela agência em 28/10/2026, no vídeo `PROJETOS/2026-10-27 IMG_8749 lustres 50 off`: "esse vai ser o padrão de edição da Eletro definitivo"). O `MODELO/` está igual ao desse projeto. Use esse vídeo como exemplo pronto. Mude o padrão só quando a agência pedir, e registre aqui.

## Marca
- **Eletro Company (Materiais elétricos e iluminação):** loja de materiais elétricos e iluminação desde 1999. Tem loja física na **Av. Tiradentes, 80 – Jardim Shangri-Lá A (Londrina)** e loja virtual que entrega em todo o Brasil. Atende desde pequenas reformas até obras corporativas e industriais: cabos flexíveis, disjuntores, mangueiras corrugadas, exaustão e iluminação. O foco do manual é **segurança e eficiência energética**.
- **Tom:** direto, de vendedor que conhece o produto. No vídeo base, o apresentador está **dentro da loja** (prateleiras e luminárias atrás), **de camisa branca**, segura o produto para a câmera e fala da promoção:
  - "Promoção relâmpago aqui na Eletro Company…"
  - "…plafon de embutir da Inlumix de 24W, tá saindo pela promoção de R$ 19,90…"
  - "…clique aqui embaixo e garanta o melhor preço de Londrina e toda a região."
- **Card final sem botão** (pedido da agência em 28/10): só o principal, ou seja, logo, endereço e entrega. O CTA fica na fala e na legenda.
- **@ do Instagram e telefone:** ainda não informados. O card final sai com o endereço e a loja virtual.

## Cores (manual)
- **Verde `#007800`:** cor principal ("Nossas cores"). Vai nas caixas (etiqueta, lista), na tela de cor e no texto de botões (quando houver). O preço e a caixa da legenda saíram da caixa verde (28/10): viraram verde-limão.
- **Branco `#ffffff`:** legenda, texto sobre o verde, endereço do card final, tela de cor branca.
- **Verde vivo `#14c832`:** tirado das capas do manual ("PROMOÇÃO DA ELETRO", o "10" de "KIT 10"). Vai na barra que risca, no ✓ da lista, na linha do antes/depois e no raio. O `#007800` puro some sobre o fundo escuro, por isso o vivo.
- **Verde-limão com degradê e brilho** (pedido da agência em 28/10, referência "PARE DE / **MOTIVAÇÃO** / DE ESPERAR" e os letreiros verdes de um reel do Pinterest): **todas as palavras-chave verdes**. São as palavras verdes da legenda, as linhas verdes da capa e do título e o **card de preço** (28/10: "esses letreiros verdes no mesmo padrão do letreiro verde" do "ACONCHEGANTE").
  - O degradê vai de `#e8ff78` em cima, passa por `#acf234` e chega a `#58cc16` embaixo (`LIME_*` no `brand.py`).
  - Em volta, um brilho verde `#96ff3c`, mais uma sombra escura justa para ler na loja clara e na camisa branca.
- **Verde escuro `#105820`** (capa "KIT 10"): fundo verde de reserva (quando não há foto). O card final usa a fachada em verde fechado (`#03260c` por cima da foto).
- **Cinza `#606060`:** texto de apoio no painel branco do produto.

## Tipografia (manual)
- **Open Sans** (título no manual): legenda (Bold), palavra grande (ExtraBold), itálicos (Bold/ExtraBold/SemiBold Italic), etiquetas pequenas e botão (ExtraBold caixa-alta).
- **Bebas Neue** (apoio no manual, e a fonte das capas "PROMOÇÃO DA ELETRO" / "KIT 10"): caixa verde, títulos, nome do produto, etiqueta. Sempre CAIXA-ALTA.
- **Archivo Black** (fora do manual, só no verde-limão: palavras da legenda e o valor/observação do preço): larga e pesada como o "MOTIVAÇÃO" da referência (28/10). Sempre CAIXA-ALTA.
- Arquivos em `MODELO/assets/fonts` (licença livre OFL). A Open Sans veio do Google Fonts (pesos fixos gerados da fonte variável).
- A referência de legenda usa uma serifada itálica no destaque ("mercadoria"). Na palavra riscada ficou a **Open Sans Italic**. A palavra verde virou verde-limão em Archivo Black (28/10).

## Logo
- **Durante o vídeo: SEM logo no alto** (pedido da agência em 27/10: "no padrão vamos ficar sem eles em cima"). O logo aparece só no card final.
  - Se algum vídeo pedir, `"logo": true` no EDL volta com a plaquinha verde `#007800` com o logo "Cor Branca" (`logo_badge.png`, 220 px, centralizada no alto). Aí `"logo_hide": [[t0, t1]]` tira o logo num trecho.
- **Card final:** logo "Cor Branca" grande sobre a fachada em verde fechado. O EC sobe com um brilho suave e o nome entra logo depois.
- **Versões em `MODELO/assets`:** `logo_original.png` (metálico verde), `logo_white.png` (EC prata + nome branco), `logo_black.png`, `logo_icon.png` / `logo_icon_white.png` (só o EC), `logo_name_white.png`, `logo_compact_white.png` (EC + nome, sem a linha de baixo).
  - Todas saem do PNG da agência (`logo_fonte.png`, 1250 px) com `brand.make_logos()`.
  - Se vier o vetor, exporte um PNG grande no lugar do `logo_fonte.png` e rode `make_logos()` e `make_badge()`.

## Elementos gráficos (do manual)
- **Linha tracejada com bolinha** (títulos das páginas do manual): na capa e no título. **No card final, não** (lá é uma linha fina e lisa, 28/10).
- **Listras diagonais finas** (capa "TOMADA AQUECENDO?"): **saíram do card final** em 28/10. Ficam só como reserva no `brand_background`.
- **⚡ raio** (selo "⚡ 40W" da capa "KIT 10"): no selo do produto, na etiqueta e no "DEPOIS".
- **Caixa verde com Bebas branca** ("LÂMPADAS TASCHIBRA"): etiqueta, lista (o preço e a legenda não, desde 28/10).
- **Barras verticais laterais** das páginas do manual: **não usei**.

## Formato
- Vertical 1080×1920 a 30 fps (Reels, Stories, TikTok).
- **Margem de segurança:** x 91–988, y 100–1681 (`MODELO/assets/margem_seguranca.jpeg`). Legenda, cards e card final ficam **sempre dentro dela**. A legenda encolhe se não couber e o `selfeval.py` reprova o que sair.
- **Cor: igual à do bruto** (pedido da agência em 27/10: "não precisa arrumar o color").
  - Sem filtro, sem LUT e sem ajuste de saturação/contraste.
  - Bruto HDR do iPhone vira SDR só com a conversão.
  - O `selfeval.py` confere as etiquetas BT.709 e se a cor bate com a do bruto (≤ 0,8 nível).
- **Cortes: só em respiros/silêncios medidos no áudio, nunca no meio da fala** (folga de ~40 ms). No fim, conferir se todas as palavras aparecem na legenda.

## Referência de edição (vídeo base IMG_4879, 14 s)
- **Formato:** apresentador **na loja**, plano médio (da cintura para cima), câmera na mão. **Mostra o produto** para a câmera, às vezes cobrindo o rosto.
- **Ritmo:** fala rápida, sem respiros longos. Vídeos de ~15 s.
- **Estrutura:**
  1. Gancho: "Promoção relâmpago aqui na Eletro Company".
  2. Produto: nome, marca e potência.
  3. Preço.
  4. CTA: "clique aqui embaixo e garanta o melhor preço de Londrina e toda a região".
  5. Card final (~2,6 s) por cima do último quadro congelado.
- **Zoom suave:** cada troca de enquadramento é um zoom de 0,5 s com ease in/out, centrado na emenda.
- **Sem "teto" vazio em cima da cabeça** (pedido da agência em 29/10: "sempre que não tiver título no teto dos vídeos, dê zoom in centralizando a pessoa"):
  - o `frame.py` acha o rosto no bruto e enquadra cada trecho: pessoa **centralizada** na horizontal e o **alto da cabeça a ~230 px do topo** no plano aberto;
  - é zoom in quando sobra parede em cima e zoom out (até o quadro inteiro) quando a cabeça já está no alto;
  - os níveis são relativos a esse enquadramento: **aberto** (loja), **médio** ×1,1 (produto), **fechado** ×1,22 (frase forte, CTA);
  - com **título no alto** (capa, título, tag, lista acima da cabeça, gancho em cima) o trecho fica com o espaço para o título;
  - **duas pessoas:** enquadramento manual (`"frame": "manual"`), com o centro entre as duas e o zoom que ainda mostra as duas inteiras.
- **Transições entre takes** (bruto que já vem montado com fala + imagens da loja). Use poucas; nem toda emenda precisa:
  - `flash` (luz acendendo) com som de interruptor (`"sfx": "switch"`) na troca da fala para as imagens;
  - `"trans": "zoom"` no trecho: zoom que empurra até a emenda e volta, com desfoque radial e whoosh;
  - as outras emendas ficam em corte seco;
  - os trechos de imagens de apoio levam `"person": false` (a legenda fica fixa no centro, sem procurar rosto nas luminárias).

## Legenda (referência `REFERENCIAS/referencia_legenda.mp4`)
Estilo da referência com as fontes e cores do manual (`animations/captions_eletro.py`, `"style": "ELC"`):
- **Pequena e limpa:** Open Sans Bold 60 branca, no peito.
  - Frases curtas (até 2 linhas de 3 palavras) que trocam rápido.
  - Cada palavra entra no tempo da fala, **desfocada → nítida** (4 quadros).
  - A linha desliza para o centro quando ganha palavra.
- **Sombra:** escura e justa, mais um halo largo, porque o apresentador usa **camisa branca** e a loja é clara.
- **Lockup na palavra forte** (o "no / EMBALAMENTO / da sua mercadoria" da referência):
  - as palavras de antes ficam pequenas em **itálico, em cima, alinhadas à esquerda** da palavra forte;
  - as de depois ficam **embaixo, alinhadas à direita**;
  - "de", "da", "a"… que sobram no fim de um lockup passam para o próximo.
- **Destaques** (no EDL; use pouco, 1 por frase no máximo):
  - `big`, **grande:** Open Sans ExtraBold branca 2,2×, **digitada** (revela da esquerda, suave).
  - `accents`, **verde-limão:** Archivo Black CAIXA-ALTA com degradê e brilho (estilo "MOTIVAÇÃO", 28/10), digitada; o brilho "acende" quando ela termina ("OPORTUNIDADE", "LUSTRE"). Antes era itálico verde.
  - `strikes`, **riscada:** Open Sans Bold Italic branca, digitada, e a **barra verde vivo risca** da esquerda. Para o que é ruim/errado ("gambiarra", "caro").
  - `keywords`, **chave:** o mesmo verde-limão com brilho, gigante (2,2×), com "pop". Para preço, potência e produto ("R$ 19,90", "24W").
  - `boxes`: **sai igual a `accents`, verde-limão com brilho e sem caixa** (pedido da agência em 28/10, no "METADE DO PREÇO": "esse letreiro também no outro estilo"). Antes era Bebas branca na caixa verde `#007800`. Para expressão, prefira listar em `accents`.
- **Troca de frase:** o bloco anterior some em 3 quadros, 2 quadros antes do novo entrar.
- **Gancho** (até `hook_end`): tudo 15 % maior.
  - `"hook_top": true` põe o gancho **acima da cabeça** (como o "um erro" da referência), mas só quando cabe dentro da margem.
  - No vídeo base a cabeça fica alta e não coube, então a legenda voltou para o peito.
- **Posição:** a 1ª linha começa **logo abaixo do meio do pescoço** (rosto do `person.json`, seguido quadro a quadro). Sem rosto, o bloco fica centrado em `"cy"` (padrão 1060). Na mesma tomada, a altura não pula.
- **Produto e etiqueta na tela:** a legenda termina acima deles (encolhe até 75 % se precisar).

## Nada na frente do rosto
- **Legenda, preço, produto e etiqueta:** sempre **do meio do pescoço para baixo**, na frente. O `selfeval.py` reprova se algo começar acima.
- **Duas pessoas no vídeo** (ex.: o Casal Eletricista, 29/10): o rastreio alterna entre os rostos e a legenda pula de altura. Use `"person": false` em todos os trechos e `"cy"` no peito, abaixo dos dois queixos (≈1040), e zoom de no máximo 1,15 para não cortar ninguém.
- **Capa, lista, título e tag:** **acima da cabeça** (`"y": "auto"`, encolhe até 72 %). Onde ainda encostarem, **ficam atrás dela**: o `build.py` recorta a pessoa (U²-Net) e a põe por cima.
- Plano médio com a cabeça alta: a capa e a lista acima da cabeça ficam pequenas. Prefira a lista com `"place": "below"`, pulando a legenda no trecho.

## Grafismos disponíveis (`animations/eletro_cards.py`)
- **topic (capa):** etiqueta branca (texto verde) + título Bebas em 1–2 linhas (branca e verde-limão com brilho) + linha tracejada. Fica no alto, acima da cabeça.
- **price** (refeito em 28/10, no padrão do "moderna e / ACONCHEGANTE" da legenda): um lockup **sem caixas**:
  - chamada pequena em itálico branco ("todos os lustres"), alinhada à esquerda do valor, em cima;
  - "de R$ 39,90" riscado pela barra verde + "por" em verde-limão (opcional);
  - **valor gigante verde-limão com degradê e brilho** (Archivo Black), que entra com "pop" e o brilho "acende";
  - observação verde-limão menor ("DO MOSTRUÁRIO"), alinhada à direita do valor, embaixo, digitada.
  - Esconde a legenda. Encolhe para caber entre o pescoço e a margem. Antes era a caixa verde com Bebas branca.
- **product:** painel branco com filete verde vivo, nome do produto em Bebas verde, detalhe em cinza e **selo "⚡ 24W"**. Fica embaixo, na frente.
- **label:** etiqueta verde inclinada com ⚡ e Bebas branca, com pop. Fica embaixo, na frente; `"bolt": false` tira o raio.
- **checklist:** lista com quadrado verde vivo e ✓ (ou 1, 2, 3 com `"numbers": true`) + caixa verde com Bebas. Cada item entra quando é falado. `"place": "below"` põe a lista na frente, abaixo do pescoço.
- **title:** frase pequena em itálico + palavra GIGANTE em Bebas branca (+ 2ª linha verde-limão com brilho) + linha tracejada, atrás da pessoa. Esconde a legenda.
  - **Só com a pessoa de lado ou pequena na tela.** Com o apresentador no centro, a cabeça cobre o meio do título ("PADR…OPEL", 29/10). Nesse caso use o **lockup de texto na frente**: card `price` sem preço (`kicker` + `value` + `note`, ex.: "menor preço em / PADRÃO COPEL / JÁ INSTALADO"), com `"sfx": false` e um `pop` em `sfx_events` (o som de dinheiro é só para preço).
- **colorcard (tela de cor):** as telas cheias da referência, com corte seco e som de interruptor.
  - Fundo verde `#007800` com a fala em branco, ou branco com a fala em verde.
  - A fala sai em letra pequena no centro, palavra por palavra (do transcript).
  - Alternar verde → branco funciona bem em 2–3 palavras rápidas.
- **flash:** luz acendendo (clarão branco frio) para transição. Use 1–2 por vídeo.
- **tag:** caixinha verde pequena.
- **broll:** trecho de outro vídeo (prateleira, produto, fachada) por cima da fala, sem o som dele.
  - Só as partes em que o produto é mostrado com calma: tire os momentos de pegar e de abaixar o produto (pedido de 29/10, kit DeWalt).
  - Cada trecho sai **travado, como num tripé**, **sem zoom** e com **corte seco** entre os trechos, sem transição (29/10: "a camada ainda ta com uma tremida, não precisa dar zoom in na camada").
  - Mesmo travado, o kit DeWalt (filmado com a câmera na mão, de cima) ainda pareceu um pouco tremido para a agência, que aprovou assim. **Para os próximos, peça o vídeo de apoio gravado com o celular apoiado.**
- **photo** (refeito em 29/10, "como se fosse quadrinhos"): **quadrinho** na frente do peito, e não mais em tela cheia:
  - a foto vem recortada em 4:5 em volta do produto (`"focus": [x, y]` muda o centro), com borda branca, cantos arredondados, sombra e leve inclinação (±4°, alternando);
  - entra com um **pop suave** (cresce com um leve passo além e assenta) e sai encolhendo;
  - tem ~46% da largura da tela (500 px) e fica do meio do pescoço para baixo: não é pequeno demais e nunca cobre o rosto;
  - a legenda some enquanto ele está na tela.
- **beforeafter:** "ANTES" (caixa branca) → linha verde varre a tela → "⚡ DEPOIS" (caixa verde). Bom para ambiente antes/depois da iluminação.
- **end** (refeito em 28/10: "mais profissional, linha do meio limpa, sem listras, verde mais fechado com a foto de fundo"):
  - **Fundo:** a foto da fachada da loja em verde (`MODELO/assets/fundo_card_final.jpg`, cópia em `REFERENCIAS/fundo card final (fachada).jpg`).
    - Leva um verde mais fechado por cima (`END_SHADE`, `"shade"` 0,55), com uma faixa mais escura atrás do texto e um zoom lento.
    - **O conjunto (logo, linha, endereço e entrega) fica centralizado no meio da tela, na vertical e na horizontal** (28/10). O letreiro da fachada aparece logo acima do logo.
  - O EC sobe e aparece com um brilho suave (sem piscar) e o nome entra logo depois.
  - **Linha:** fina e lisa, abrindo do centro (sem tracejado e sem bolinha).
  - **Embaixo da linha, o principal:** o endereço em branco ("Av. Tiradentes, 80 · Londrina"), a entrega/loja virtual e o @, quando houver.
  - **Sem botão** (28/10, "pode tirar, deixe o principal"). Se um vídeo pedir, `"cta": "..."` no card `end` põe um botão branco em pílula.
  - **Som:** whoosh e um chime no logo.

## Som
- **Voz** é a protagonista. A **trilha** sobe +10 dB depois da última fala.
- **Trilha: lo-fi** (pedido da agência em 28/10: "não quero que nem esse do modelo que está infantil demais, quero um Lo-fi").
  - **Referência:** `REFERENCIAS/referencia_trilha_lofi_IMG_8755.MOV`, um lo-fi house a 121 BPM, com bumbo em todo tempo, chimbal rápido, acordes quentes e abafados (Am9 → Dm9, 2 compassos cada) e muito grave.
  - **A trilha é sintetizada nessa mesma vibe** (`"music": {"style": "lofi"}`): piano elétrico, pad, sub, bateria macia com "bombeamento", fita oscilando e chiado de vinil. Sem direito autoral.
  - **Nível:** −20 dB em relação à voz. A parte que o celular toca (acima de 250 Hz) fica ~26 dB abaixo da voz, como na trilha antiga.
  - **Não usar** música baixada do Instagram, do TikTok ou do YouTube (direito autoral; post de empresa pode ficar mudo ou ser removido). Para um áudio em alta, gerar uma versão sem trilha (`"music": null`) e escolher o som no app, na biblioteca comercial.
  - A trilha antiga ("upbeat", com arpejo) foi recusada: "infantil demais".
- **Efeitos** (todos sintetizados, com corpo na faixa do alto-falante de celular, ~6–12 dB abaixo da voz):
  - **Gancho:** impacto curto no destaque do gancho. Os outros destaques ficam sem som.
  - **Eletro:** faísca elétrica (`zap`) no flash e no selo ⚡; interruptor (`switch`) na tela de cor; marcador (`swipe`) na palavra riscada e no "de R$" do preço.
  - **Outros:** pop na etiqueta, dinheiro no preço, clique no "clique", whoosh na capa/lista e whoosh suave na troca de zoom (no máx. 1 a cada 4 s).
  - **Sem amontoar:** som da legenda que cai até 0,3 s antes ou 0,6 s depois de um som de card sai.
  - Para silenciar um card: `"sfx": false` no EDL. Sem o whoosh automático das trocas de zoom: `"sfx": "cards"`.
- **Master:** −14 LUFS, pico ≤ −1,5 dBTP.

## Cuidados
- **Preço e condições** ("de/por", "no Pix", "até acabar o estoque", parcelas) **exatamente como falados/aprovados**. Na dúvida, perguntar antes de pôr na tela.
- **Nomes certos na legenda:** **Eletro Company** (o motor ouve "Electro"), **plafon** (ouve "plafão"), **Inlumix** (ouve "Ilumix"), **Taschibra**, **LED**, **Londrina**. O `transcribe.py` corrige esses. O que faltar vai em `"fix"` no EDL.
- **Marca e modelo do produto:** conferir na caixa do produto que aparece no vídeo.
- **Placas de carro de terceiros** (fachada, estacionamento): se aparecerem legíveis, desfocar com `MODELO/blur_plates.py`.
