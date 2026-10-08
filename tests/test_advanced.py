import unittest
from shapely.geometry import box,mapping,Point,LineString
from studio import study,read_geojson
from advanced import least_cost,temporal,export_contract

def layer(g):return {'type':'FeatureCollection','features':[{'type':'Feature','properties':{},'geometry':mapping(g)}]}
class AdvancedTests(unittest.TestCase):
 def test_index_and_mixed_geometry(self):
  layers={'site':layer(box(-48,-16,-47.98,-15.98)),'inside':layer(box(-48,-16,-47.99,-15.99)),'outside':layer(box(-47.8,-16,-47.79,-15.99)),'point':layer(Point(-47.995,-15.995)),'line':layer(LineString([(-48,-16),(-47.99,-15.99)]))}
  r=study(layers,'site');self.assertLess(r['spatial_index']['intersecting_pairs'],r['spatial_index']['possible_pairs']);self.assertEqual(next(x for x in r['layers'] if x['layer']=='point')['points_inside'],1)
  self.assertGreater(next(x for x in r['layers'] if x['layer']=='line')['clipped_length_m'],0)
 def test_temporal_conservation(self):
  layers={'site':layer(box(-48,-16,-47.98,-15.98)),'old':layer(box(-48,-16,-47.99,-15.99)),'new':layer(box(-47.995,-16,-47.985,-15.99))}
  r=temporal(layers,'old','new','site','EPSG:32723','2025-01-01','2026-01-01');self.assertAlmostEqual(r['after_ha']-r['before_ha'],r['gain_ha']-r['loss_ha']);self.assertGreater(r['gain_ha'],0)
  with self.assertRaises(ValueError):temporal(layers,'old','new','site','EPSG:32723','2026-01-01','2025-01-01')
 def test_resistance_detour_and_barrier(self):
  r=least_cost([[1,1,1],[1,100,1],[1,1,1]],[1,0],[1,2],1);self.assertEqual(r['weighted_cost'],4);self.assertNotIn((1,1),r['path'])
  self.assertFalse(least_cost([[1,None,1]],[0,0],[0,2])['reachable'])
 def test_review_contract_and_geojson(self):
  layers={'a':layer(box(-48,-16,-47.99,-15.99))};rows=[{'layer':'a','reviewed':True,'reviewer':'Test','category':'vegetation','date':'2026-01-01'}]
  self.assertEqual(export_contract({},layers,rows)['schema'],'biomadata.spatial-study.v1')
  rows[0]['reviewed']=False
  with self.assertRaises(ValueError):export_contract({},layers,rows)
  self.assertEqual(read_geojson(layer(Point(-48,-16)))['type'],'FeatureCollection')
