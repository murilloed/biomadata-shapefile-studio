import argparse,json,zipfile
from pathlib import Path
import shapefile
from pyproj import CRS
from studio import read_layer,study,build_map

def main():
 p=argparse.ArgumentParser();p.add_argument('--input',help='Directory containing polygon shapefiles and .prj');p.add_argument('--boundary',default='study_area');p.add_argument('--output',default='output');a=p.parse_args();o=Path(a.output);o.mkdir(parents=True,exist_ok=True)
 if a.input:folder=Path(a.input)
 else:
  folder=o/'sample';folder.mkdir(exist_ok=True)
  rings={'study_area':[(-48,-16),(-48,-15.985),(-47.98,-15.985),(-47.98,-16),(-48,-16)],'vegetation':[(-47.997,-15.998),(-47.997,-15.988),(-47.987,-15.988),(-47.987,-15.998),(-47.997,-15.998)],'observation_zone':[(-47.992,-15.995),(-47.992,-15.986),(-47.982,-15.986),(-47.982,-15.995),(-47.992,-15.995)]}
  for name,ring in rings.items():
   with shapefile.Writer(str(folder/name),shapeType=shapefile.POLYGON) as w:w.field('label','C');w.poly([ring]);w.record(name)
   (folder/(name+'.prj')).write_text(CRS.from_epsg(4326).to_wkt(),encoding='utf-8')
 layers={f.stem:read_layer(f) for f in sorted(folder.glob('*.shp'))}
 report=study(layers,a.boundary);report['synthetic']=not bool(a.input)
 (o/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');(o/'map.html').write_text(build_map(layers),encoding='utf-8')
 if not a.input:
  with zipfile.ZipFile(o/'sample-shapefiles.zip','w',zipfile.ZIP_DEFLATED) as z:
   for f in folder.iterdir():z.write(f,f.name)
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
