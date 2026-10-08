import io,json
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from studio import load_zip,read_geojson,study,build_map
from territory import understand
from advanced import temporal,review_registry,least_cost,export_contract,route_svg
st.set_page_config(page_title='BiomaData Shapefile Studio',layout='wide')
st.title('BiomaData — Shapefile Studio')
st.write('Camadas vetoriais, índice espacial, comparação temporal e resistência ecológica. Processamento local; mapas usam serviços externos. Nenhum modelo de IA treinado.')
upload=st.file_uploader('ZIP com Shapefiles (.prj obrigatório)',type=['zip'])
geo=st.file_uploader('Camadas adicionais GeoJSON WGS84',type=['geojson','json'],accept_multiple_files=True)
if st.button('Usar demonstração sintética'):
 sample=Path(__file__).parent/'output/sample-shapefiles.zip'
 if sample.exists():st.session_state['sample_data']=sample.read_bytes()
 else:st.info('Execute python demo.py primeiro para gerar a amostra.')
source=upload.getvalue() if upload else st.session_state.get('sample_data')
if source or geo:
 try:
  layers=load_zip(io.BytesIO(source)) if source else {}
  for file in geo:
   name=Path(file.name).stem
   if name in layers:raise ValueError('Nome de camada duplicado: '+name)
   layers[name]=read_geojson(json.loads(file.getvalue()))
  names=list(layers)
  if st.button('Interpretar limites e gerar camadas territoriais'):
   territorial,derived=understand(layers);st.json(territorial)
   components.html(build_map({**layers,**derived}),height=600)
   st.download_button('Baixar camadas geradas GeoJSON',json.dumps(derived,ensure_ascii=False),file_name='derived-layers.json')
  default=next((i for i,name in enumerate(names) if any('CD_MUN' in f.get('properties',{}) for f in layers[name]['features'])),0)
  boundary=st.selectbox('Camada poligonal limite da área de estudo',names,index=default)
  visible=st.multiselect('Camadas do mapa',names,default=names)
  if visible:components.html(build_map({n:layers[n] for n in visible}),height=550)
  st.subheader('Categorias revisadas')
  st.caption('Categorias são atribuídas por uma pessoa; não são inferidas automaticamente.')
  registry=[]
  reviewer=st.text_input('Responsável pela revisão')
  for name in names:
   category=st.selectbox('Categoria: '+name,['vegetation','water','infrastructure','study_boundary','observation','other'],index=3 if name==boundary else 5,key='cat_'+name)
   registry.append({'layer':name,'category':category,'reviewer':reviewer,'date':str(st.date_input('Data de referência: '+name,key='date_'+name)),'reviewed':st.checkbox('Confirmo a categoria: '+name,key='review_'+name)})
  if st.button('Gerar estudo espacial'):
   report=study(layers,boundary);st.json(report)
   st.download_button('Baixar estudo JSON',json.dumps(report,indent=2),file_name='study.json')
  st.subheader('Comparação temporal')
  before=st.selectbox('Camada anterior',names);after=st.selectbox('Camada posterior',names)
  date_before=st.date_input('Data anterior');date_after=st.date_input('Data posterior')
  if st.button('Comparar períodos'):
   result=temporal(layers,before,after,boundary,study(layers,boundary)['metric_crs'],str(date_before),str(date_after))
   st.json({k:v for k,v in result.items() if k!='change_layers'})
   components.html(build_map({boundary:layers[boundary],**result['change_layers']}),height=450)
   st.download_button('Baixar comparação',json.dumps(result),file_name='temporal.json')
  st.subheader('Exportação para integração')
  st.caption('Contrato de dados versionado. Nenhum envio à aplicação BiomaData é realizado.')
  if st.button('Preparar pacote BiomaData'):
   package=export_contract(study(layers,boundary),layers,registry)
   st.download_button('Baixar pacote revisado',json.dumps(package,ensure_ascii=False),file_name='biomadata-study.json')
 except Exception as e:st.error(str(e))
st.subheader('Resistência ecológica — caminho de menor custo')
st.caption('Envie JSON com grid (valores positivos ou null para barreiras), start/end [linha,coluna] e cell_m. Sem calibração ecológica, o resultado é exploratório.')
resistance=st.file_uploader('Grade de resistência JSON',type=['json'],key='resistance')
if resistance and st.button('Calcular caminho'):
 try:
  data=json.loads(resistance.getvalue());result=least_cost(data['grid'],data['start'],data['end'],data['cell_m']);st.json(result);components.html(route_svg(data['grid'],result),height=260)
  st.download_button('Baixar caminho',json.dumps(result),file_name='least-cost.json')
 except Exception as e:st.error(str(e))
