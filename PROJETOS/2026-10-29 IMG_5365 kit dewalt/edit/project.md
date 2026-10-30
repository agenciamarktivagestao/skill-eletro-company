# 2026-10-29 · IMG_5365 · Kit DeWalt

- **Brutos:**
  - `../IMG_5365.MOV`, a fala;
  - `../IMG_5020.MOV`, o vídeo de apoio (iPhone HDR em pé, guardado deitado com rotação −90°).
  - Saíram de `01 ENVIAR AQUI/` na aprovação, em 29/10.
- **Final:** `final.mp4`, com 26.4 s em 1080×1920 a 30 fps. Hardlink em `02 FINALIZADOS/2026-10-29 IMG_5365 kit dewalt.mp4`.
- **Preço na tela:** de R$ 1.399,90 por R$ 998,50, conferido com a fala.
- **Aprovação:** em 29/10 ("a camada ainda ta tremida, mas ta bom, aprovado").

## Este vídeo
- **Nomes corrigidos:** "DeWalt" (o reconhecimento ouviu "De Vault") e "Eletro Company".
- **Grafismos:**
  - placa "Kit DeWalt / parafusadeira + furadeira" com o selo "2 baterias";
  - preço de/por, com um corte fechando no valor;
  - etiqueta "Poucas unidades".
- **Camada (IMG_5020, no mudo):** ficaram só os trechos em que ele mostra o produto; os momentos de pegar e de abaixar foram cortados.
  - 5,7–8,4 s: a máquina de pé e girando, depois as baterias.
  - 13,4–17,6 s: a máquina de lado, o kit montado na maleta e ele encaixando a bateria.

## Ajustes da camada
1. **HDR:** o vídeo de apoio é HDR, e a conversão antiga do MODELO (`zscale`) não existe no ffmpeg do Homebrew. Entrou a conversão pela VideoToolbox (`build.sdr_proxy`).
2. **Rotação:** a primeira cópia SDR girou duas vezes e ampliou o b-roll. A cópia passou a guardar a imagem original com a marca de rotação.
3. **"Toda tremida e lagada":** o `zoompan` do ffmpeg andava de pixel inteiro. Troquei pelo zoom com subpixel e pela estabilização do arquivo inteiro, e o tremor caiu de 1,5 para 0,7 px por quadro.
4. **"Ainda ta com uma tremida, não precisa dar zoom in":** sem zoom, corte seco entre os trechos e cada trecho travado como num tripé. O movimento da câmera caiu de 1,4 para 0,5 px por quadro.
5. **Aprovado** com a observação de que ainda treme um pouco. O que sobra vem da câmera na mão, filmando de cima e inclinando. Para os próximos, o ideal é gravar o vídeo de apoio com o celular apoiado.
6. **Correção depois da aprovação (29/10):** a agência viu um "bug" no meio dos primeiros trechos da parafusadeira: um quadro do apresentador entre dois trechos da camada, em 6,633 s.
   - **Causa:** a `base.mkv` guarda o tempo em milissegundos, e o card que começava em 199/30 s ligava 0,1 ms tarde demais.
   - **Correção:** no MODELO, o card agora liga meio quadro antes, e o `selfeval.py` ganhou a checagem "camadas opacas sem buraco".
   - O `final.mp4` foi refeito e o hardlink em `02 FINALIZADOS` foi trocado. O final antigo ficou como `final_v1.mp4`.
