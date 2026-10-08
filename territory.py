"""Recognize administrative/biome attributes and derive territorial overlays."""
import argparse,io,json,re,csv
from pathlib import Path
from pyproj import Geod
from shapely import orient_polygons
from shapely.geometry import shape,mapping
from shapely.ops import unary_union
from studio import load_zip,build_map

def geodesic_km2(g):
    if g.is_empty:return 0.0
    # Normalize ring orientations so holes subtract from ellipsoidal area.
    g=orient_polygons(g)
    if g.geom_type=='MultiPolygon':return sum(geodesic_km2(p) for p in g.geoms)
    if g.geom_type!='Polygon':return 0.0
    return abs(Geod(ellps='WGS84').geometry_area_perimeter(g)[0])/1e6

def features(g,props):
    return {'type':'FeatureCollection','features':[] if g.is_empty else [{'type':'Feature','properties':props,'geometry':mapping(g)}]}

def understand(layers):
    inventory=[];municipal=[];biomes=[]
    for name,data in layers.items():
        fields=sorted({k for f in data['features'] for k in f.get('properties',{})})
        kind='municipal_boundary' if 'CD_MUN' in fields and 'NM_MUN' in fields else ('biome_boundary' if 'Bioma' in fields else 'unclassified')
        warnings=[]
        if any('\ufffd' in str(v) for f in data['features'] for v in f.get('properties',{}).values()):warnings.append('Attribute text contains replacement characters; original values retained, review labels.')
        inventory.append({'layer':name,'suggested_category':kind,'fields':fields,'features':len(data['features']),'reviewed':False,'warnings':warnings})
        for f in data['features']:
            item=(name,f)
            if kind=='municipal_boundary':municipal.append(item)
            elif kind=='biome_boundary' and str(f['properties'].get('Bioma','')).casefold()=='cerrado':biomes.append(item)
    if not biomes or not municipal:raise ValueError('Expected Cerrado biome and municipal fields CD_MUN/NM_MUN')
    biome=unary_union([shape(f['geometry']) for _,f in biomes]);derived={};rows=[]
    for name,f in municipal:
        g=shape(f['geometry']);inside=g.intersection(biome);outside=g.difference(biome)
        props=f['properties'];code=str(props['CD_MUN']);area=geodesic_km2(g);inside_area=geodesic_km2(inside)
        row={'municipality_code':code,'name_original':props['NM_MUN'],'source_layer':name,'area_attribute_km2':props.get('AREA_KM2'),'computed_area_km2':area,'inside_cerrado_km2':inside_area,'outside_cerrado_km2':geodesic_km2(outside),'inside_percent':100*inside_area/area if area else None}
        rows.append(row)
        derived[code+'_inside_cerrado']=features(inside,{**props,'derived_relation':'inside_cerrado'})
        if not outside.is_empty:derived[code+'_outside_cerrado']=features(outside,{**props,'derived_relation':'outside_cerrado'})
    union=unary_union([shape(f['geometry']) for _,f in municipal])
    derived['municipalities_union']=features(union,{'derived_relation':'municipality_union'})
    return {'schema':'biomadata.territory-study.v1','trained_model':False,'method':'Attribute schema recognition; polygon intersections in WGS84; ellipsoidal areas on WGS84','inventory':inventory,'municipalities':rows,'biome_area_attribute_km2':biomes[0][1]['properties'].get('Area_km2'),'biome_computed_area_km2':geodesic_km2(biome),'municipal_union_area_km2':geodesic_km2(union),'limitations':['Category suggestions require human review.','These files contain boundaries, not vegetation observations or temporal data.','Intersection percentages reflect supplied cartographic boundaries; not legal certification.','Area differences can arise from cartographic detail, projection and boundary overlap.']},derived

def main():
    p=argparse.ArgumentParser();p.add_argument('zipfile');p.add_argument('--output',default='output/territory');a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    layers=load_zip(io.BytesIO(Path(a.zipfile).read_bytes()));report,derived=understand(layers)
    (out/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    folder=out/'layers';folder.mkdir(exist_ok=True)
    for name,data in {**layers,**derived}.items():
        safe=re.sub(r'[^\w.-]','_',name)
        (folder/(safe+'.geojson')).write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
    (out/'map.html').write_text(build_map({**layers,**derived}),encoding='utf-8')
    municipal_layers={name:data for name,data in layers.items() if any('CD_MUN' in f['properties'] for f in data['features'])}
    (out/'map-municipalities.html').write_text(build_map({**municipal_layers,**derived}),encoding='utf-8')
    with (out/'municipalities.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(report['municipalities'][0]));w.writeheader();w.writerows(report['municipalities'])
    print('Input layers:',len(layers),'derived:',len(derived))
    for row in report['municipalities']:print(row['municipality_code'],round(row['inside_percent'],4),'percent in Cerrado')
if __name__=='__main__':main()
