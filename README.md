# BiomaData — Shapefile Studio

Protótipo independente para importar camadas poligonais Shapefile, visualizar mapas com camadas e produzir estudo espacial baseado em regras. Não integra automaticamente a aplicação original do BiomaData e não treina ML.

## Executar
```bash
python -m pip install -r requirements.txt
python demo.py
python -m unittest discover -s tests -v
```
Abre `output/map.html`: mapa com controle de camadas. Relatório em `output/report.json`. A demo gera três shapefiles sintéticos e `sample-shapefiles.zip`.

## Interface de upload local
```bash
python -m pip install -r requirements-app.txt
streamlit run app.py
```
Envie ZIP com `.shp`, `.shx`, `.dbf` e `.prj` na raiz; selecione a camada limite, escolha camadas visíveis e clique em Gerar estudo espacial. Máximo 50 MB descompactados. Aceita pontos, linhas e polígonos válidos. Nomes de arquivos e camadas devem ser únicos. O processamento usa arquivos temporários locais; não envia shapefiles para um servidor de análise. HTML de mapa usa CDN e tiles OpenStreetMap: há requisições externas para exibir o mapa.

## Dados reais via CLI
```bash
python demo.py --input /pasta/shapefiles --boundary nome_limite --output output/real
```
Exige `.prj`; reprojeta para WGS84 na exibição e escolhe UTM local para áreas. Limitado a áreas regionais (extensão máxima de 3 graus) entre latitudes UTM. Analise a projeção apropriada antes do uso real.

## Estudo inteligente
União por camada evita dupla contagem interna, interseção mede cobertura dentro do limite e cruzamentos entre camadas indicam sobreposições. Notas sinalizam camadas sem interseção. São regras determinísticas explicáveis; não classificação automática, diagnóstico ecológico ou conclusão legal. Percentuais de camadas diferentes podem se sobrepor e não devem ser somados.

## Evolução implementada

- Índice STRtree para cruzamentos espaciais; apenas pares que se intersectam são listados. Pares ausentes têm interseção vazia.
- Shapefiles de pontos, multipontos, linhas e polígonos; GeoJSON WGS84 na interface. Área limite deve ser poligonal. Pontos e linhas têm contagem/comprimento, sem interpretação de cobertura por área.
- Comparação de duas camadas poligonais e datas: ganho, perda, estabilidade e variação líquida, com novas camadas no mapa. Diferenças não atribuem causas ambientais.
- Registro de categorias fornecidas e confirmadas por revisor e data. Não há classificação por ML.
- Caminho de menor custo em grade JSON de resistências positivas, barreiras null e tamanho métrico da célula; Dijkstra com quatro vizinhos e custo médio das células multiplicado pelo passo. Visualização da grade não é georreferenciada. Não lê GeoTIFF nesta versão.
- Pacote `biomadata.spatial-study.v1` com relatório, camadas WGS84, revisão e SHA-256. Exportação local apenas: nenhum endpoint da aplicação original foi alterado ou acionado.

## Reproduzir a evolução
```bash
python demo.py
python evolution_demo.py
```
Gera `output/evolution-report.json`, `map-evolved.html`, `integration-package.json`, `temporal-layers.json`, `resistance-sample.json` e `resistance-route.svg`. Todas as novas amostras são sintéticas. A interface permite enviar JSON de resistência com `grid`, `start`, `end` e `cell_m`.

## Próximas etapas restantes
Validar CRS e comparabilidade temporal em dados autorizados, calibrar resistência por espécie/contexto, importar GeoTIFF georreferenciado e implementar receptor autenticado do contrato na aplicação BiomaData. Não existe avaliação com arquivos de clientes nesta publicação.
