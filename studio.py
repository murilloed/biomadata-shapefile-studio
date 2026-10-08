"""Shapefile import, metric overlay study and selectable web map layers."""
import json,zipfile,tempfile,html
from pathlib import Path
import shapefile,folium
from pyproj import CRS,Transformer
from shapely.geometry import shape,mapping
from shapely.ops import transform,unary_union

def read_layer(path):
 path=Path(path)
 for suffix in ['.shp','.shx','.dbf','.prj']:
  if not path.with_suffix(suffix).is_file():raise ValueError('Missing companion: '+suffix)
 crs=CRS.from_wkt(path.with_suffix('.prj').read_text())
 convert=Transformer.from_crs(crs,4326,always_xy=True).transform
 with shapefile.Reader(str(path)) as reader:
  fields=[f[0] for f in reader.fields[1:]];features=[]
  for record in reader.iterShapeRecords():
   g=shape(record.shape.__geo_interface__)
   if g.is_empty or not g.is_valid or g.geom_type not in ['Polygon','MultiPolygon','Point','MultiPoint','LineString','MultiLineString']:raise ValueError('Valid point, line or polygon features required')
   g=transform(convert,g)
   if not (-180<=g.bounds[0]<=g.bounds[2]<=180 and -90<=g.bounds[1]<=g.bounds[3]<=90):raise ValueError('Invalid geographic coordinates')
   features.append({'type':'Feature','geometry':mapping(g),'properties':dict(zip(fields,list(record.record)))})
 return {'type':'FeatureCollection','features':features}

def load_zip(data):
 with tempfile.TemporaryDirectory() as folder:
  with zipfile.ZipFile(data) as z:
   infos=z.infolist()
   if sum(i.file_size for i in infos)>50_000_000:raise ValueError('ZIP exceeds 50 MB uncompressed')
   for info in infos:
    if info.is_dir():continue
    p=Path(info.filename)
    if p.name!=info.filename or p.suffix.lower() not in ['.shp','.shx','.dbf','.prj','.cpg']:raise ValueError('ZIP must contain only root-level shapefile components')
    (Path(folder)/p.name).write_bytes(z.read(info))
  paths=sorted(Path(folder).glob('*.shp'))
  if not paths:raise ValueError('No .shp in ZIP')
  return {p.stem:read_layer(p) for p in paths}

def study(layers,boundary_name):
 if boundary_name not in layers:raise ValueError('Select an analysis boundary')
 polygons={name:unary_union([shape(f['geometry']) for f in data['features']]) for name,data in layers.items()}
 boundary=polygons[boundary_name]
 if boundary.geom_type not in ['Polygon','MultiPolygon'] or boundary.is_empty or boundary.area<=0:raise ValueError('Empty analysis boundary')
 center=boundary.centroid
 if not (-80<center.y<84):raise ValueError('Demo supports UTM latitudes only')
 if boundary.bounds[2]-boundary.bounds[0]>3 or boundary.bounds[3]-boundary.bounds[1]>3:raise ValueError('Use a regional study area; extent exceeds demo limits')
 zone=int((center.x+180)//6)+1;epsg=(32600 if center.y>=0 else 32700)+min(zone,60)
 to_metric=Transformer.from_crs(4326,epsg,always_xy=True).transform
 area=transform(to_metric,boundary);rows=[];uncovered=[]
 for name,poly in polygons.items():
  if name==boundary_name:continue
  clipped=area.intersection(transform(to_metric,poly));percent=100*clipped.area/area.area
  rows.append({'layer':name,'geometry_type':poly.geom_type,'area_ha':clipped.area/10000,'coverage_percent':percent,'clipped_length_m':clipped.length if poly.geom_type in ['LineString','MultiLineString'] else None,'points_inside':sum(area.covers(transform(to_metric,shape(f['geometry']))) for f in layers[name]['features']) if poly.geom_type=='Point' else (sum(area.covers(p) for p in transform(to_metric,poly).geoms) if poly.geom_type=='MultiPoint' else None)})
  if clipped.is_empty:uncovered.append(name)
 from shapely.strtree import STRtree
 names=[n for n in polygons if n!=boundary_name]
 clipped=[area.intersection(transform(to_metric,polygons[n])) for n in names]
 tree=STRtree(clipped);pairs=[];candidates=0
 for i,g in enumerate(clipped):
  for j in tree.query(g,predicate='intersects'):
   j=int(j)
   if j<=i:continue
   candidates+=1;pairs.append({'layers':[names[i],names[j]],'overlap_ha':g.intersection(clipped[j]).area/10000})
 return {'trained_model':False,'method':'deterministic polygon union/intersection; local UTM area','metric_crs':'EPSG:'+str(epsg),'spatial_index':{'type':'STRtree','intersecting_pairs':candidates,'possible_pairs':len(names)*(len(names)-1)//2},'boundary':boundary_name,'boundary_area_ha':area.area/10000,'layers':rows,'pairwise_overlap':pairs,'study_notes':['Layers with no overlap: '+', '.join(uncovered)] if uncovered else ['All thematic layers intersect the study boundary.'],'limitations':['Layer names are user-provided, not inferred land-use classes.','Coverage of separate layers may overlap; percentages must not be added.','No ecological/legal diagnosis; temporal comparisons require reviewed dates and comparable layers.','Regional planar analysis; projection selection requires review for real projects.']}

def build_map(layers):
 features=[shape(f['geometry']) for data in layers.values() for f in data['features']]
 if not features:raise ValueError('No polygons')
 bounds=unary_union(features).bounds
 m=folium.Map(location=[(bounds[1]+bounds[3])/2,(bounds[0]+bounds[2])/2],zoom_start=13,tiles='OpenStreetMap')
 colors=['#2de2e6','#3baf73','#efb66b','#ef7680']
 for i,(name,data) in enumerate(layers.items()):
  color=colors[i%len(colors)]
  folium.GeoJson(data,name=html.escape(name),style_function=lambda feature,c=color:{'color':c,'fillColor':c,'weight':2,'fillOpacity':.25}).add_to(m)
 folium.LayerControl(collapsed=False).add_to(m);m.fit_bounds([[bounds[1],bounds[0]],[bounds[3],bounds[2]]]);return m.get_root().render()

def read_geojson(data):
 if data.get('type')!='FeatureCollection' or data.get('crs'):raise ValueError('WGS84 FeatureCollection without legacy CRS required')
 for feature in data.get('features',[]):
  g=shape(feature['geometry'])
  if not g.is_valid or g.is_empty or g.geom_type not in ['Point','MultiPoint','LineString','MultiLineString','Polygon','MultiPolygon']:raise ValueError('Unsupported geometry')
  if not (-180<=g.bounds[0]<=g.bounds[2]<=180 and -90<=g.bounds[1]<=g.bounds[3]<=90):raise ValueError('Invalid WGS84 coordinates')
 return data
