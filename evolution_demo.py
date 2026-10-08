import json
from pathlib import Path
from shapely.geometry import box,Point,LineString,mapping
from studio import read_layer,study,build_map
from advanced import temporal,least_cost,export_contract,route_svg
folder=Path('output');folder.mkdir(exist_ok=True)
layers={p.stem:read_layer(p) for p in sorted((folder/'sample').glob('*.shp'))}
def layer(g):return {'type':'FeatureCollection','features':[{'type':'Feature','properties':{},'geometry':mapping(g)}]}
layers['vegetation_before']=layer(box(-47.999,-15.999,-47.989,-15.989))
layers['monitoring_points']=layer(Point(-47.995,-15.995))
layers['access_line']=layer(LineString([(-47.999,-15.999),(-47.982,-15.986)]))
report=study(layers,'study_area');report['synthetic']=True
comparison=temporal(layers,'vegetation_before','vegetation','study_area',report['metric_crs'],'2025-01-01','2026-01-01')
resistance={'grid':[[1,1,1,1,1],[1,20,20,20,1],[1,1,1,1,1]],'start':[1,0],'end':[1,4],'cell_m':30}
route=least_cost(**resistance)
registry=[{'layer':name,'category':'study_boundary' if name=='study_area' else 'other','reviewer':'synthetic demo reviewer','date':'2026-01-01','reviewed':True} for name in layers]
package=export_contract(report,layers,registry)
summary={'synthetic':True,'trained_model':False,'study':report,'temporal':{k:v for k,v in comparison.items() if k!='change_layers'},'resistance':route,'integration':{'schema':package['schema'],'sha256':package['sha256'],'status':package['integration_status']}}
(folder/'evolution-report.json').write_text(json.dumps(summary,indent=2));(folder/'integration-package.json').write_text(json.dumps(package));(folder/'resistance-sample.json').write_text(json.dumps(resistance));(folder/'temporal-layers.json').write_text(json.dumps(comparison['change_layers']));(folder/'map-evolved.html').write_text(build_map({**layers,**comparison['change_layers']}));print(json.dumps(summary,indent=2))

(folder/'resistance-route.svg').write_text(route_svg(resistance['grid'],route))
