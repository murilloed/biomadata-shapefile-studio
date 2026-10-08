"""Temporal overlays, reviewed category registry, resistance-grid paths and export contract."""
import math,heapq,json,hashlib
from datetime import date
from pyproj import Transformer
from shapely.geometry import shape,mapping
from shapely.ops import transform,unary_union

def temporal(layers,before,after,boundary,crs,date_before,date_after):
    if date.fromisoformat(date_before)>=date.fromisoformat(date_after):raise ValueError('Before date must precede after date')
    convert=Transformer.from_crs(4326,crs,always_xy=True).transform
    def polygons(name):
        features=[shape(f['geometry']) for f in layers[name]['features']]
        if any(g.geom_type not in ['Polygon','MultiPolygon'] for g in features):raise ValueError('Temporal layers must be polygonal')
        return transform(convert,unary_union(features))
    area=polygons(boundary);old=polygons(before).intersection(area);new=polygons(after).intersection(area)
    loss=old.difference(new);gain=new.difference(old);stable=old.intersection(new)
    back=Transformer.from_crs(crs,4326,always_xy=True).transform
    return {'dates':[date_before,date_after],'before_ha':old.area/10000,'after_ha':new.area/10000,'gain_ha':gain.area/10000,'loss_ha':loss.area/10000,'stable_ha':stable.area/10000,'net_change_ha':(new.area-old.area)/10000,'change_layers':{name:{'type':'FeatureCollection','features':[{'type':'Feature','properties':{'change':name},'geometry':mapping(transform(back,g))}]} for name,g in [('gain',gain),('loss',loss),('stable',stable)] if not g.is_empty},'limitation':'Differences in supplied polygon layers; not automatic environmental event attribution.'}

def review_registry(rows):
    result=[]
    for row in rows:
        if not row.get('reviewed') or not str(row.get('reviewer','')).strip():raise ValueError('Category requires named human review')
        date.fromisoformat(row['date'])
        if row['category'] not in ['vegetation','water','infrastructure','study_boundary','observation','other']:raise ValueError('Unknown category')
        result.append(dict(row))
    return result

def least_cost(grid,start,end,cell_m=30):
    if not grid or not grid[0] or any(len(row)!=len(grid[0]) for row in grid):raise ValueError('Rectangular grid required')
    if not math.isfinite(cell_m) or cell_m<=0:raise ValueError('Positive metric cell size required')
    for row in grid:
        for value in row:
            if value is not None and (not math.isfinite(value) or value<=0):raise ValueError('Positive finite resistance or null barrier required')
    h,w=len(grid),len(grid[0]);start=tuple(start);end=tuple(end)
    for r,c in [start,end]:
        if not (0<=r<h and 0<=c<w) or grid[r][c] is None:raise ValueError('Endpoint outside traversable grid')
    distances={start:0};parent={};heap=[(0,start)]
    while heap:
        cost,(r,c)=heapq.heappop(heap)
        if cost!=distances[(r,c)]:continue
        if (r,c)==end:
            route=[end]
            while route[-1]!=start:route.append(parent[route[-1]])
            route.reverse();return {'reachable':True,'path':route,'weighted_cost':cost,'distance_m':(len(route)-1)*cell_m,'neighbors':4,'limitation':'Supplied resistance values require ecological calibration; a least-cost path is not a validated corridor.'}
        for dr,dc in [(1,0),(-1,0),(0,1),(0,-1)]:
            rr,cc=r+dr,c+dc
            if not (0<=rr<h and 0<=cc<w) or grid[rr][cc] is None:continue
            nxt=(rr,cc);candidate=cost+(grid[r][c]+grid[rr][cc])/2*cell_m
            if candidate<distances.get(nxt,float('inf')):distances[nxt]=candidate;parent[nxt]=(r,c);heapq.heappush(heap,(candidate,nxt))
    return {'reachable':False,'path':[],'weighted_cost':None,'distance_m':None,'neighbors':4}

def export_contract(report,layers,registry):
    review_registry(registry)
    if any(row['layer'] not in layers for row in registry):raise ValueError('Unknown registry layer')
    if set(row['layer'] for row in registry)!=set(layers):raise ValueError('Every layer requires category review')
    payload={'schema':'biomadata.spatial-study.v1','source':'shapefile-studio','coordinate_system':'EPSG:4326','report':report,'layers':layers,'category_review':registry,'integration_status':'export_only_not_connected'}
    payload['sha256']=hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest();return payload


def route_svg(grid,route):
    h,w=len(grid),len(grid[0]);cells=[];path=set(tuple(p) for p in route.get('path',[]))
    for r,row in enumerate(grid):
        for c,value in enumerate(row):
            color='#efb66b' if (r,c) in path else ('#071526' if value is None else ('#833b48' if value>5 else '#247f66'))
            cells.append(f'<rect x="{c*40}" y="{r*40}" width="39" height="39" fill="{color}"/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w*40} {h*40}">'+''.join(cells)+'</svg>'
