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
Envie ZIP com `.shp`, `.shx`, `.dbf` e `.prj` na raiz; selecione a camada limite, escolha camadas visíveis e clique em Gerar estudo espacial. Máximo 50 MB descompactados. Aceita polígonos/multipolígonos válidos. Nomes de arquivos e camadas devem ser únicos. O processamento usa arquivos temporários locais; não envia shapefiles para um servidor de análise. HTML de mapa usa CDN e tiles OpenStreetMap: há requisições externas para exibir o mapa.

## Dados reais via CLI
```bash
python demo.py --input /pasta/shapefiles --boundary nome_limite --output output/real
```
Exige `.prj`; reprojeta para WGS84 na exibição e escolhe UTM local para áreas. Limitado a áreas regionais (extensão máxima de 3 graus) entre latitudes UTM. Analise a projeção apropriada antes do uso real.

## Estudo inteligente
União por camada evita dupla contagem interna, interseção mede cobertura dentro do limite e cruzamentos entre camadas indicam sobreposições. Notas sinalizam camadas sem interseção. São regras determinísticas explicáveis; não classificação automática, diagnóstico ecológico ou conclusão legal. Percentuais de camadas diferentes podem se sobrepor e não devem ser somados.

## Próximas etapas
Índice espacial, upload de outras geometrias, indicadores temporais, categorias revisadas, resistência ecológica e integração autorizada com BiomaData. Não existe avaliação com arquivos de clientes nesta publicação.
