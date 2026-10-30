# Eletro Company: pasta de edição

Esta pasta é só da **Eletro Company** (materiais elétricos e iluminação, loja na Av. Tiradentes, 80 em Londrina e loja virtual). O usuário (Agência Marktiva) fala português (pt-BR); responda sempre em português. Ele coloca os vídeos brutos em `01 ENVIAR AQUI/` e pede a edição.
- **Leia `ESTILO.md` antes de propor qualquer coisa:**
  - cores, fontes e logo vêm do manual em `REFERENCIAS/`;
  - a legenda vem de `REFERENCIAS/referencia_legenda.mp4`;
  - o formato, o tom e o CTA vêm de `REFERENCIAS/video_base_IMG_4879.MOV`;
  - o resumo visual está em `REFERENCIAS/padrao_eletro.jpg`.
- O `CLAUDE.md` da pasta `Downloads/` é de outro cliente. Aqui vale só este.
- **O padrão é definitivo** desde 28/10/2026 (aprovado no `PROJETOS/2026-10-27 IMG_8749 lustres 50 off`, que é o exemplo pronto). Não mude o estilo do `MODELO/` sem pedido da agência.

A edição roda **no próprio Mac**, com o Python do ambiente `~/.venvs/edicao` (Python 3.12 com PIL, numpy, scipy, OpenCV, onnxruntime, sherpa-onnx, PyMuPDF e fontTools) e o ffmpeg do Homebrew. Os modelos ficam em `~/models`: Parakeet para a transcrição, Haar para o rosto e U²-Net para o recorte da pessoa. Antes dos comandos:
```
PY=~/.venvs/edicao/bin/python
```

## Quando chegar material novo em `01 ENVIAR AQUI/`
1. **Criar o projeto:** `PROJ="PROJETOS/<AAAA-MM-DD> <IMG_xxxx> <tema curto>"`.
   - Brutos em `$PROJ/` (o vídeo da fala e os vídeos de apoio da loja/produto, se vierem separados); fotos em `$PROJ/fotos/`.
   - `cp -R MODELO "$PROJ/edit"`. Todos os comandos abaixo rodam em `$PROJ/edit/`.
   - Ainda **não** mova o bruto: ele sai de `01 ENVIAR AQUI/` só na aprovação. Até lá, aponte o `"source"` do EDL para ele com o caminho completo.
2. **Transcrever e cortar:**
   - **Transcrição:** `$PY transcribe.py <bruto>` → `transcript.json` + `transcript.txt` (pt, tempo por palavra, Parakeet TDT v3). Leva segundos.
   - **Nomes:** leia o `transcript.txt` e corrija nomes (Eletro Company, plafon, Inlumix, Taschibra, LED, Londrina, valores "R$ 19,90", potência "24W").
     - As correções fixas ficam em `FIXES` no `transcribe.py`.
     - As do vídeo vão em `"captions": {"fix": {...}}`. Com espaço na chave, junta palavras: `"eletro company": "Eletro Company"`.
   - **Produto:** confira marca, modelo e potência na caixa que aparece no vídeo.
   - **Placas de carro de terceiros legíveis:** `blur_plates.py` (instruções no topo do script); depois use o `_placas.mp4` como `"source"`.
   - **Cortes só em respiros:** meça o áudio (RMS a cada 20 ms; respiro < −45 dB) e corte com ~40 ms de folga de cada lado. Os tempos do transcript são aproximados (±0,1 s); o áudio manda.
   - **EDL inicial:** `$PY make_cuts.py <bruto>` → `edl.json` (corta pausas ≥ 0,3 s e troca o enquadramento a cada ~3 s).
   - **Olhe os quadros** (extraia alguns com ffmpeg). `anchor` vai no corpo/rosto.
   - **Enquadramento:** escreva o nível de cada trecho (zoom 1.0 = aberto, 1.15 = médio/produto, 1.25 = fechado/CTA). O `frame.py` (o `build.py` chama sozinho) acha o rosto e grava zoom/anchor: pessoa centralizada e sem "teto" vazio em cima da cabeça. Com duas pessoas, use `"frame": "manual"`. Corte tropeços e repetições.
   - **B-roll:** quando ele fala do produto, da loja ou da entrega, use as imagens de apoio que vierem.
3. **Propor o plano em português e ESPERAR a aprovação** antes de renderizar:
   - duração final, trechos cortados, enquadramentos e b-roll;
   - gancho (`hook_end`; `hook_top` se couber acima da cabeça);
   - destaques da legenda (1 por frase no máximo): palavra grande, verde-limão com brilho (palavra ou expressão), riscada, chave (verde-limão gigante). A caixa verde da legenda saiu em 28/10 (`boxes` sai verde-limão);
   - grafismos (capa, preço de/por, produto, etiqueta, lista, tela de cor, título, flash, card final) e textos (endereço, @; o card final é sem botão);
   - pergunte, se fizer sentido, o que o cliente quer destacar;
   - **conferir preço e condições** com o que foi falado.
4. **Montar o `edl.json`.** A referência completa está em `MODELO/edl_exemplo.json`. Legenda: `"style": "ELC"`.
5. **Renderizar:** `$PY build.py --preview`. O script faz, nesta ordem:
   - a base: cortes + zoom suave + quadro congelado;
   - o `person.py`: segue o rosto quadro a quadro (legenda/preço do meio do pescoço para baixo) e recorta a pessoa (capa/título ATRÁS dela);
   - os grafismos (`animations/eletro_cards.py`) e a legenda (`animations/captions_eletro.py`), quando o EDL muda;
   - a mixagem do áudio e a composição do `preview.mp4`.

   Um vídeo de 15 s leva ~30 s. Mudou só script ou asset? Use `--force`.
6. **Revisar antes de mostrar:**
   - `$PY selfeval.py preview.mp4 base.mkv`. Confere:
     - quadros = EDL, áudio = vídeo e sincronismo em cada corte;
     - margem de segurança e legenda/preço do meio do pescoço para baixo (pelo `person.json`);
     - etiquetas de cor BT.709 e cor igual à do bruto;
     - −14 LUFS / pico ≤ −1,5 dBTP;
     - camadas opacas (b-roll, antes/depois, tela de cor) sem buraco: em cada quadro da janela, o vídeo tem que ser a camada, não a base.

     Gera `contact.jpg` e `card_edges.jpg`.
   - **Abra as duas folhas com Read** e confira:
     - legenda e grafismos nunca na frente do rosto (títulos acima da cabeça ou atrás dela);
     - tudo dentro da margem;
     - palavra forte sem estourar a largura;
     - legenda legível na camisa branca;
     - cards sem quadro faltando nas bordas.
   - Mande o preview com `SendUserFile`. Ele já fica salvo em `$PROJ/edit/preview.mp4`.
7. **Ajustes:** o `build.py` guarda as versões anteriores (`preview_v1.mp4`, `edl_v1.json`, …). A base só é refeita se os cortes mudarem.
8. **Na aprovação:**
   - `$PY build.py` → `final.mp4`; rode o `selfeval.py` de novo.
   - Salve um hardlink em `02 FINALIZADOS/<AAAA-MM-DD> <IMG_xxxx> <tema>.mp4` (`ln`) e mova o bruto de `01 ENVIAR AQUI/` para `$PROJ/` (atualize o `"source"` do EDL).
   - Registre a sessão em `$PROJ/edit/project.md` (pedido, decisões, ajustes, o que o cliente aprovou/recusou) e atualize o `ESTILO.md` se surgir regra nova.
   - Com a permissão do usuário, apague os intermediários pesados: `base.mkv`, `captions.mov`, `cards/`, `person_mask.mkv`, `mix_raw.wav`, `sdr_*.mov`.

## Para retomar um projeto antigo
Use `$PROJ/edit/edl.json`, `transcript.json`, os brutos e as fotos do projeto. Se o `MODELO/` tiver mudado, copie os scripts novos para `$PROJ/edit/` e rode o `build.py --force`.

## Pendências da pasta (checar no primeiro uso)
- **@ do Instagram:** não informado; o card final sai sem ele (`HANDLE` no `brand.py` ou `"handle"` no card `end`).
- **Logo:** extraído do PNG da agência (1250 px). Se vier o vetor (SVG/PDF), exporte um PNG grande como `MODELO/assets/logo_fonte.png` e rode `brand.make_logos()` e `brand.make_badge()`.
- **Palavras verdes:** verde-limão com degradê e brilho em Archivo Black (pedido de 28/10, fora das fontes do manual). Confirmar com o cliente se essa fonte fica.

## Detalhes técnicos já resolvidos no MODELO (não desfazer)
- **Cortes no grid de quadros:** a fonte vira 30 fps antes do `trim` por número de quadro. O áudio de cada trecho é cortado nos mesmos tempos, com `aresample first_pts=0 + apad + atrim`. Desvio medido: 0,5 ms.
- **Cards:** entram meio quadro antes, com `eof_action=repeat`, para não perder o primeiro nem o último quadro. O `enable` do overlay também liga meio quadro antes. A `base.mkv` guarda o tempo em milissegundos (199/30 = 6,63333 vira 6,633), e com uma folga de 0,1 ms o 1º quadro de um card que começava num tempo assim saía sem a camada: um quadro do apresentador entre dois b-rolls (29/10). Cards opacos (broll, antes/depois, tela de cor) ficam por baixo da legenda. A foto é um quadrinho com alfa, na frente da pessoa (29/10).
- **Saída:** usa `-frames:v` igual ao total do EDL; o logo em loop (quando ligado) tem um quadro a mais.
- **Pausa final:** usa `hold` (último quadro congelado) por baixo do card final. A trilha é sintetizada (sem música de artista): lo-fi por padrão, na vibe de `REFERENCIAS/referencia_trilha_lofi_IMG_8755.MOV` (`sound._lofi`, `MUSIC_DB`). Não baixar música do Instagram, TikTok ou YouTube.
- **Concat da base:** depois do `concat` vem `settb=1/30,setpts=N,fps=30:eof_action=pass` antes do `tpad`. Sem isso, o congelado sumia.
- **Zoom suave:** o ffmpeg corta numa tela k × 1080×1920 sem zoom. O `build_base` aplica o zoom de cada quadro com subpixel (`cv2.warpAffine`), com ease in/out em `ZOOM_EASE` = 0,5 s centrado na emenda.
- **Rosto (`person.py`):** é seguido pelo caminho (mediana móvel de ±12 quadros). Candidatos longe desse caminho são descartados (um "rosto" falso no fundo jogava a legenda para baixo).
- **Legenda (`captions_eletro.py`):**
  - a posição usa o pescoço no intervalo em que o bloco fica na tela (`t`–`t_end` no `bboxes.json`, que o `selfeval.py` também usa);
  - o "pop" da chave nunca passa da margem;
  - o bloco antigo começa a sumir 2 quadros antes do novo entrar;
  - a legenda lê o `bboxes.json` dos cards e termina acima do produto/etiqueta na tela (por isso os cards são renderizados antes);
  - o risco fica no meio da altura do "x" (minúsculas) ou da maiúscula.
- **Rosto x b-roll:** com b-roll, foto, antes/depois ou tela de cor na tela, o `build.py` não recola a pessoa da base por cima.
- **B-roll:** o `build.crop_for` (janela 9:16 com zoom/anchor) faz o recorte.
  - **Trava por trecho** (`lock_moves` no `eletro_cards.py`; `"stab": false` desliga):
    - o OpenCV mede o movimento da câmera no trecho (com RANSAC, ignorando as mãos);
    - cada quadro volta para a posição média, como num tripé;
    - o corte fixo é o menor que esconde as bordas (até 1,06), aplicado nos planos Y/U/V;
    - sem zoom animado e com corte seco entre os trechos (pedido de 29/10).
    - A suavização do arquivo inteiro (testada antes) ainda "flutuava".
  - O `"push"` (opcional, desligado no padrão) é feito com subpixel: o `zoompan` do ffmpeg andava de pixel inteiro e tremia.
- **Recursos do EDL:**
  - `"zoom_ease": 0` num trecho: troca seca de zoom (para emendar em cima de um corte que já vem no bruto);
  - `"person": false` no trecho: imagens de apoio que já vêm no bruto, sem o apresentador. O `person.py` não procura rosto ali (achava "rostos" nas luminárias e a legenda pulava de altura) e a legenda fica centrada em `"cy"`;
  - `"trans": "zoom"` no trecho que entra: transição entre takes. O zoom empurra até a emenda e volta (±0,2 s), com desfoque radial e um whoosh (`TRANS_*` no `build.py`);
  - `"sfx": "cards"`: só os efeitos dos cards, da legenda e das transições, sem o whoosh automático nas trocas de zoom;
  - **logo no alto:** o padrão é **sem logo** durante o vídeo (pedido da agência em 27/10; `LOGO_ON_VIDEO` no `brand.py`). `"logo": true` volta com a plaquinha e `"logo_hide"` tira o logo de um trecho;
  - na checklist, `"place": "below"` vai automaticamente para a frente da pessoa.
- **Volume dos efeitos:** `SFX_DB` no `build.py`, pico em dB relativo ao RMS da fala.
  - Cada efeito fica ~6–12 dB abaixo da fala. Com o pico abaixo do RMS da fala, eles sumiam.
  - Grave abaixo de ~200 Hz não sai no alto-falante de celular: todo efeito novo precisa de corpo entre 250 Hz e 6 kHz (a faísca `zap` não tem o 120 Hz por isso).
- **Composição:** `brand._safe_composite` cola sem máscara (`paste(im, pos)` + `alpha_composite`). Com máscara, a transparência saía ao quadrado.
- **Loudnorm:** duas passadas com alvo −2,5 dBTP, para o AAC não passar de −1,5 (com o grave do lo-fi, o AAC subia o pico até −1,4).
- **ffmpeg 9 do Homebrew:** não tem `drawtext`. Texto em imagem sempre via PIL.
- **Cor igual à do bruto:**
  - Quadros que passam por pipe (rawvideo) não têm etiqueta. Sem declarar a entrada, o ffmpeg 9 supunha BT.601 e convertia para BT.709 sozinho (imagem ~1 % mais escura e esverdeada).
  - A entrada do pipe é declarada BT.709 (`BT709` no `build.py`) e a saída leva as 3 etiquetas (`setparams` + `write_colr`).
  - Grafismos RGBA viram vídeo com conversão explícita BT.709 (`RGBA_TO_YUV`), e o recorte da pessoa não passa por RGB.
  - **HDR (HLG/PQ do iPhone) → SDR:** o ffmpeg do Homebrew não tem `zscale` (a antiga `HDR_CHAIN` falhava). O `build.sdr_proxy` converte com a VideoToolbox (`scale_vt`), a mesma conversão do iPhone ao exportar em SDR, numa cópia `sdr_<nome>.mov` em `edit/`, uma vez. Serve para bruto e b-roll. A cópia guarda a imagem como foi gravada e a mesma marca de rotação do original (girar a imagem na conversão girava duas vezes e ampliava o b-roll). Só conversão, sem ajuste de cor.
  - O `selfeval.py` reprova se a cor de um trecho diferir do bruto em mais de 0,8 nível. Nos trechos com zoom, ele compara com a mesma janela recortada no bruto (desde 29/10; com o enquadramento automático, quase nenhum trecho fica em zoom 1.0).
