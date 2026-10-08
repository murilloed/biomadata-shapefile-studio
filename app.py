import io,json
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from studio import load_zip,study,build_map
st.set_page_config(page_title='BiomaData Shapefile Studio',layout='wide')
st.title('BiomaData — Shapefile Studio')
st.write('Carregue um ZIP com camadas poligonais (.shp, .shx, .dbf e .prj), selecione o limite e gere o estudo. Processamento local; mapa base usa OpenStreetMap e bibliotecas externas.')
upload=st.file_uploader('ZIP com Shapefiles',type=['zip'])
if st.button('Usar demonstração sintética'):
 sample=Path(__file__).parent/'output/sample-shapefiles.zip'
 if sample.exists():st.session_state['sample_data']=sample.read_bytes()
 else:st.info('Execute python demo.py primeiro para gerar a amostra.')
source=upload.getvalue() if upload else st.session_state.get('sample_data')
if source:
 try:
  layers=load_zip(io.BytesIO(source))
  boundary=st.selectbox('Camada limite da área de estudo',list(layers))
  visible=st.multiselect('Camadas do mapa',list(layers),default=list(layers))
  if visible:components.html(build_map({n:layers[n] for n in visible}),height=600)
  if st.button('Gerar estudo espacial'):
   report=study(layers,boundary);st.json(report)
   st.download_button('Baixar estudo JSON',json.dumps(report,indent=2),file_name='study.json',mime='application/json')
 except Exception as e:st.error(str(e))
