#!/usr/bin/env python3
"""Site geometry, orientation and derived constraints for the Boriyad campus.
Emits data/site.json. All lengths in metres. CRS: UTM Zone 37N, Adindan."""
import json, math, os

P = [("P1",464112.500,996833.918),("P2",464109.918,996749.453),
     ("P3",464041.882,996761.305),("P4",464058.980,996827.622),
     ("P5",464066.779,996828.861)]
BH = [("BH-1",464073,996713,7.0),("BH-2",464091,996705,15.0),("BH-3",464081,996697,10.0),
      ("BH-4",464095,996691,5.6),("BH-5",464077,996674,3.5),("BH-6",464099,996665,3.5)]
ORIGIN = (464000.0, 996700.0)   # local model origin; Rhino world (0,0,0) maps here

def local(x,y): return (round(x-ORIGIN[0],3), round(y-ORIGIN[1],3))
poly = [local(x,y) for _,x,y in P]

def shoelace(pts):
    s=0
    for i in range(len(pts)):
        x1,y1=pts[i]; x2,y2=pts[(i+1)%len(pts)]
        s+=x1*y2-x2*y1
    return abs(s)/2
area = shoelace(poly)

edges=[]
for i in range(len(P)):
    a,x1,y1=P[i]; b,x2,y2=P[(i+1)%len(P)]
    dx,dy=x2-x1,y2-y1; L=math.hypot(dx,dy)
    az=math.degrees(math.atan2(dx,dy))%360
    edges.append({"from":a,"to":b,"length_m":round(L,2),"azimuth_deg":round(az,2),
                  "off_nearest_cardinal_deg":round(min(az%90,90-az%90),2)})

def west_at(y):   # local y -> local x of the west boundary, valid 61.305 <= y <= 127.622
    return round(41.882 + 0.25783*(y-61.305),3)
def east_at(y):   # valid 49.453 <= y <= 133.918
    return round(109.918 + 0.030569*(y-49.453),3)

site = {
 "project":"Boriyad Youth Academy, Ashewa Meda, Oromia, Ethiopia",
 "crs":{"system":"UTM Zone 37N","datum":"Adindan","units":"metres",
        "note":"The geotechnical report states hand-held GPS on UTM Adindan. Its borehole northings fall 36-84 m south of this polygon; the datum basis is unresolved. See docs/02-ground-and-survey-review.md."},
 "model_origin":{"easting":ORIGIN[0],"northing":ORIGIN[1],
   "instruction":"Place Rhino world origin (0,0,0) at this easting/northing at reduced level 0.00. Model +X = true East, +Y = true North, +Z = up. All coordinates below are LOCAL (world minus origin)."},
 "boundary_survey_coordinates":[{"id":n,"easting":x,"northing":y,
     "local_x":local(x,y)[0],"local_y":local(x,y)[1]} for n,x,y in P],
 "boundary_polygon_local":poly,
 "boundary_closed":True,
 "area_m2":round(area,2),
 "area_stated_in_brief_m2":4621.80,
 "edges":edges,
 "extent":{"east_west_m":round(max(p[0] for p in poly)-min(p[0] for p in poly),2),
           "north_south_m":round(max(p[1] for p in poly)-min(p[1] for p in poly),2)},
 "boundary_functions":{
   "west_edge_P3_P4":"x = 41.882 + 0.25783*(y - 61.305)   valid 61.305 <= y <= 127.622",
   "east_edge_P1_P2":"x = 109.918 + 0.030569*(y - 49.453) valid 49.453 <= y <= 133.918",
   "south_edge_P2_P3":"y = 49.453 + 0.174196*(109.918 - x) valid 41.882 <= x <= 109.918",
   "north_edge_P4_P5":"y = 127.622 + 0.158867*(x - 58.980) valid 58.980 <= x <= 66.779",
   "north_edge_P5_P1":"y = 128.861 + 0.110606*(x - 66.779) valid 66.779 <= x <= 112.500"},
 "largest_inscribed_cardinal_rectangle":{
   "x_min":58.9,"y_min":58.5,"width_ew_m":51.0,"depth_ns_m":68.0,"area_m2":3468,
   "note":"Brute-force result at 1 m resolution. This is the orthogonal build envelope; the residual ~1,150 m2 is a western and southern wedge suited to landscape, drop-off and the agricultural plot."},
 "orientation":{
   "true_north_is_model_plus_Y":True,
   "finding":"The plot is very nearly cardinally aligned. East boundary 1.75 deg off true north-south; north boundary 6.31 deg off true east-west. Building parallel to the boundaries therefore also aligns the long elevations north and south. Do NOT rotate the grid; the site grain and the solar optimum coincide.",
   "preferred_classroom_bar_axis_deg":90.0,
   "preferred_bar_axis_tolerance_deg":7.0},
 "context":{
   "roads":{"east":"assumed principal road (Ambo Road corridor) - TO BE CONFIRMED",
            "south":"secondary road / junction at the south-west",
            "north":"possible frontage - TO BE CONFIRMED",
            "west":"lower-density residential fabric, dense small plots"},
   "setbacks_assumed_m":{"east":2.0,"north":2.0,"south":2.0,"west":3.0,
     "warning":"Road reservation NOT yet quantified. Treat as a parameter; re-run if a reservation is imposed."},
   "altitude_m":2324,"latitude_deg":8.97,"longitude_deg":38.78},
 "climate":{
   "koppen":"Weina Dega / subtropical highland",
   "mean_annual_temp_C":15.9,"dry_season_day_max_C":23.3,"dry_season_night_min_C":7.3,
   "wet_season_max_C":21.0,"wet_season_min_C":10.0,
   "annual_rainfall_mm":1089,"annual_sunshine_hours":2439,
   "solar":{"noon_altitude_range_deg":[65,85],
            "zenith_passage_dates":["approx 20 April","approx 23 August"],
            "sun_north_of_zenith":"late April to late August (kiremt rains, mostly diffuse)",
            "sun_south_of_zenith":"remaining 8.5 months (clear dry season)",
            "critical_orientations":"East and west. 07:00-09:00 and 15:30-18:00 the sun sits at 10-30 deg altitude. Horizontal shading is ineffective at these angles; use vertical fins.",
            "overheating_design_condition":"March to April, end of the long dry season",
            "design_rule":"North and south facades: horizontal overhang 1.2 m. East and west facades: vertical fins or a veranda of 2.5-3.0 m."},
   "wind":{"dry_season_Oct_May":{"direction":"E to NE","character":"northeast trades, dry and dust-laden"},
           "wet_season_Jun_Sep":{"direction":"SW","character":"moist monsoon, rain-driving"},
           "typical_speed_ms":[2,4]}},
 "ground":{
   "source":"NATM Engineering Plc, October 2024, for Three M JY Trading Plc. Boreholes lie OUTSIDE this polygon - indicative only.",
   "strata":[{"layer":"A","desc":"soft to medium stiff dark grey high plastic silty CLAY (black cotton)","thickness_m":[2.0,3.0]},
             {"layer":"B","desc":"stiff to very stiff reddish brown high plastic silty CLAY with sand and gravel","base_depth_m":[3.5,15.0]},
             {"layer":"C","desc":"weak to moderately weak highly weathered closely jointed fractured vesicular BASALT","top_depth_m":[3.5,15.0]}],
   "rockhead_depth_by_bh_m":{n:d for n,_,_,d in BH},
   "groundwater":"none encountered to 10-15 m; surface water only in the rains; site described as swampy and nearly flat",
   "free_swell_pct_range":[10,130],"plasticity_index_range":[22,63],
   "expansive_soil":"SEVERE. FW 120-130 pct with PI 45-63 at 1.5-3.0 m. Active zone assumed 2.5-4.0 m.",
   "allowable_bearing_kPa_design":275,
   "allowable_bearing_kPa_report_recommendation":364,
   "bearing_note":"Report adopts BH-3; BH-2 is weaker. Carry 275 kPa until site-specific boreholes say otherwise.",
   "founding_depth_m":3.0,
   "basement_slab_depth_m":4.0,
   "seismic":{"zone":3,"pga_g":0.10,"importance_class":"III (school)","gamma_I":1.2,
              "design_pga_g":0.12,"code":"ES EN 1998-1:2015",
              "note":"The report states I = 1.0, which is wrong for a school. Plan regularity matters: avoid re-entrant corners and torsional irregularity; separate volumes with movement joints."},
   "boreholes_reported":[{"id":n,"easting":x,"northing":y,"rockhead_m":d,
                          "inside_site_polygon":False} for n,x,y,d in BH]},
 "services":{
   "water_demand_m3_per_day":30,"storage_days":2,"bulk_tank_m3":80,"roof_service_tank_m3":25,
   "wastewater_m3_per_day":[25,40],
   "sanitation":"Waterborne. Art.8.2(13)/8.3(17) specify pits, which cannot stack. On-site packaged treatment (baffled reactor plus planted gravel filter) required; no soakaway is possible in this clay.",
   "rainwater_harvest_m3_per_year":2100,
   "note":"Suspended ground-floor slab everywhere there is no basement. No high-water-demand trees (eucalyptus) within 1.5x mature height of any footing."}
}
os.makedirs("data",exist_ok=True)
json.dump(site, open("data/site.json","w"), indent=2)
print(f"area {site['area_m2']} m2, extent {site['extent']}")
for e in edges: print(f"  {e['from']}-{e['to']:<4} {e['length_m']:>7.2f} m  az {e['azimuth_deg']:>7.2f}  off-cardinal {e['off_nearest_cardinal_deg']:.2f}")
print("west_at(80)=",west_at(80)," west_at(109)=",west_at(109)," east_at(68)=",east_at(68))
