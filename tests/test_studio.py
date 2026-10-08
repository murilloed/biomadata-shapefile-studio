import unittest,io,zipfile,tempfile
from pathlib import Path
from shapely.geometry import box,mapping
import shapefile
from pyproj import CRS
from studio import study,load_zip,read_layer,build_map

def layer(g):return {'type':'FeatureCollection','features':[{'type':'Feature','properties':{},'geometry':mapping(g)}]}
class StudioTests(unittest.TestCase):
 def test_overlay_and_layers(self):
  layers={'site':layer(box(-48,-16,-47.99,-15.99)),'cover':layer(box(-48,-16,-47.99,-15.99))}
  r=study(layers,'site');self.assertAlmostEqual(r['layers'][0]['coverage_percent'],100);self.assertGreater(r['boundary_area_ha'],0)
  text=build_map(layers);self.assertIn('L.control.layers',text);self.assertIn('cover',text)
 def test_import_and_missing_projection(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'site'
   with shapefile.Writer(str(path)) as w:w.field('id','N');w.poly([[(-48,-16),(-48,-15.99),(-47.99,-15.99),(-47.99,-16),(-48,-16)]]);w.record(1)
   with self.assertRaises(ValueError):read_layer(path.with_suffix('.shp'))
   path.with_suffix('.prj').write_text(CRS.from_epsg(4326).to_wkt());self.assertEqual(len(read_layer(path.with_suffix('.shp'))['features']),1)
 def test_archive_paths_and_empty_boundary(self):
  data=io.BytesIO()
  with zipfile.ZipFile(data,'w') as z:z.writestr('../outside.shp','bad')
  data.seek(0)
  with self.assertRaises(ValueError):load_zip(data)
  with self.assertRaises(ValueError):study({'empty':{'features':[]}},'empty')
