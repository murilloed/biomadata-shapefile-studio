import unittest
from shapely.geometry import box,mapping
from territory import understand,geodesic_km2
class TerritoryTests(unittest.TestCase):
 def test_partial_overlay_and_inventory(self):
  def layer(g,p):return {'features':[{'geometry':mapping(g),'properties':p}]}
  layers={'biome':layer(box(-48,-16,-47.99,-15.98),{'Bioma':'Cerrado','Area_km2':1}),'municipality':layer(box(-48,-16,-47.98,-15.98),{'CD_MUN':'1','NM_MUN':'Test','AREA_KM2':1})}
  report,derived=understand(layers);row=report['municipalities'][0]
  self.assertAlmostEqual(row['inside_percent'],50,delta=.1);self.assertIn('1_outside_cerrado',derived);self.assertFalse(report['inventory'][0]['reviewed'])
 def test_missing_semantics_and_geodesic_hole(self):
  with self.assertRaises(ValueError):understand({})
  full=box(-48,-16,-47.98,-15.98);hole=box(-47.995,-15.995,-47.985,-15.985)
  self.assertLess(geodesic_km2(full.difference(hole)),geodesic_km2(full))
