#!/usr/bin/env python3
"""Single source of truth for the Boriyad schedule of accommodation.

Reconciles the client space programme (school_space_program.docx, Oct 2026)
against Qajeelfama Istaandaardii Manneen Barnootaa Oromiyaa, Lakk. 04/2016.
Emits data/program.json and markdown tables.

Rule: where both specify the same facility, adopt the larger. Where the
guideline mandates a facility the client omitted, add it. Client-only rooms
are kept (they exceed the guideline and are not in conflict).
"""
import json, os, math

# room = (key, label, client_each, client_no, art, guide_each, guide_no, adopt_each, adopt_no, note)
# client_each/guide_each of None = not specified in that source

KG = [
    ("kg_class_prekg","Pre-KG classroom",      49,6,  "8.1(1)",63,None, 63,6, "Guideline classroom is 63 m2 (7x9), not 49"),
    ("kg_class_kg","KG classroom",             49,6,  "8.1(1)",63,None, 63,6, ""),
    ("kg_class_prep","Prep classroom",         49,6,  "8.1(1)",63,None, 63,6, ""),
    ("kg_golee","Golee learning commons",    None,0,  "17(1)", 60,3,   60,3, "Five learning corners per Art.17(1); pooled per 6-class cluster"),
    ("kg_director","Director's office",        20,1,  "8.1(2)",20,1,   20,1, ""),
    ("kg_vicedir","Vice-director / team leader",20,1, "-",   None,None,20,1, "Client addition"),
    ("kg_staff","Staff room",                  56,1,  "8.1(3)",72,1,   72,1, "Guideline 72 m2 (8x9)"),
    ("kg_foodstore","Food store",            None,0,  "8.1(4)",36,1,   36,1, "Guideline-mandated, omitted by client"),
    ("kg_sickbay","Sick bay / rest room",      12,1,  "8.1(5)",20,2,   20,2, "Guideline 2 no. at 20 m2; client first-aid room absorbed"),
    ("kg_dining","Children's dining",          80,1,  "8.1(6)",20,4,   80,1, "Client single 80 m2 room = guideline 4x20"),
    ("kg_toilets","Toilet block, segregated",   7,2,  "8.1(7)",12,6,   12,6, "Guideline 12 m2 (3x4) x6 with adjacent handwashing"),
    ("kg_guard","Guard room",                None,0,  "8.1(8)", 9,1,    9,1, "Guideline-mandated, omitted by client"),
    ("kg_montessori","Montessori / pedagogy",  20,1,  "-",   None,None,20,1, "Client addition"),
    ("kg_tv","TV room",                        56,1,  "-",   None,None,56,1, "Client addition"),
    ("kg_nap","Nap room",                      49,1,  "-",   None,None,49,1, "Client addition"),
    ("kg_hall","Meeting hall",                100,1,  "-",   None,None,100,1,"Client addition"),
    ("kg_store","Store room",                  16,1,  "-",   None,None,16,1, ""),
    ("kg_shower","Shower",                    1.5,2,  "-",   None,None,1.5,2,""),
    ("kg_record","Record and photocopy room",  36,1,  "-",   None,None,36,1, ""),
]

PRIMARY = [
    ("pr_class","Learning classroom",          49,35, "8.2(1)",56,None, 56,35,"Guideline 56 m2 (7x8), not 49"),
    ("pr_director","Director's office",        20,2,  "8.2(2)",24,1,   24,2, "Client asks 2; guideline unit area 24"),
    ("pr_secretary","Secretary office",        12,1,  "-",   None,None,12,1, "Client addition"),
    ("pr_staff","Staff room",                  80,1,  "8.2(5)",120,2,  120,1,"Guideline 120 m2 (10x12)"),
    ("pr_staffcafe","Staff cafeteria",         56,1,  "8.2(5)",None,None,56,1,"Client splits cafeteria from staff room"),
    ("pr_dept","Departmental room",            30,2,  "8.2(6)",24,4,   30,4, "Art.8.2(6) = 96 m2 for 4; client 30 each adopted"),
    ("pr_library","Library / reading room",   100,2,  "8.2(4)",180,2,  180,2,"Guideline 180 m2 (12x15)"),
    ("pr_envkit","Environmental science kit room, G1-6",42,1,"8.2(11)",64,2,64,2,"Client single 42 m2 lab is below guideline"),
    ("pr_scilab","General science laboratory, G7-8",None,0,"8.2(12)",64,2,64,2,"Guideline-mandated"),
    ("pr_genstore","General store",            30,1,  "8.2(17)",36,1,  36,1, ""),
    ("pr_foodstore","Food store",            None,0,  "8.2(15)",42,1,  42,1, "Guideline-mandated, omitted by client"),
    ("pr_hall","Meeting room / hall",         100,1,  "-",   None,None,100,1,"Client addition"),
    ("pr_nurse","Nurse / first-aid room",      12,1,  "-",   None,None,12,1, ""),
    ("pr_ict","ICT laboratory",                56,2,  "8.2(20)",63,1,  63,2, "Guideline 63 m2 (7x9), 40 computers, 20 MB"),
    ("pr_dining","Student dining hall",        80,2,  "8.2(16)",120,2, 120,2,"Guideline 120 m2 (8x15)"),
    ("pr_handwash","Hand-washing area",         1,2,  "8.2(13)",None,None,2,4,"Adjacent to each toilet block"),
    ("pr_toilet","Student toilet block",       10,2,  "8.2(13)",20,None,20,9,"1 pit per 25 students: 1750/25 = 70 pits, 8 per 20 m2 block"),
    ("pr_guard","Guard room",                   4,2,  "8.2(21)",9,1,    9,2, ""),
    ("pr_cleaner","Cleaners' room",             4,1,  "-",   None,None, 4,1, ""),
    ("pr_stafftoilet","Staff toilet",           6,2,  "-",   None,None, 6,2, ""),
    ("pr_daycare","Day care room",           None,0,  "8.2(7)",32,1,   32,1, "Guideline-mandated, omitted by client"),
    ("pr_exam","Examination printing and store",None,0,"8.2(8)",56,1,  56,1, "Guideline-mandated, omitted by client"),
    ("pr_records","Records and student register",None,0,"8.2(9)",35,1, 35,1, "Guideline-mandated, omitted by client"),
    ("pr_matprod","Teaching-material production",None,0,"8.2(10)",56,1,56,1, "Guideline-mandated, omitted by client"),
    ("pr_girls","Girls' hygiene room",       None,0,  "8.2(14)",23.31,2,23.31,2,"Guideline-mandated, omitted by client"),
    ("pr_sen","Special-needs support centre",None,0,  "8.2(18)",72,2,  72,2, "Guideline-mandated, omitted by client"),
    ("pr_inclusive","Inclusive special class",None,0, "8.2(19)",56,1,  56,1, "Guideline-mandated, omitted by client"),
]

CENTRAL = [
    ("co_md","Managing director",              30,1,"-",None,None,30,1,""),
    ("co_principal","Principal",               25,1,"-",None,None,25,1,""),
    ("co_secretary","Secretary",               12,1,"-",None,None,12,1,""),
    ("co_academic","Academic director",        20,1,"-",None,None,20,1,""),
    ("co_quality","Quality audit and data",    30,1,"-",None,None,30,1,""),
    ("co_record","Record officer",             30,1,"-",None,None,30,1,""),
    ("co_hrm","HRM and finance",               20,1,"-",None,None,20,1,""),
    ("co_cashier","Cashier and accountant",    12,1,"-",None,None,12,1,""),
    ("co_toilet","Toilet",                      2,2,"-",None,None, 2,2,""),
    ("co_store","Store",                       30,1,"-",None,None,30,1,""),
]

SECONDARY = [
    ("hs_class","Classroom",                   49,16,"8.3(1)",56,None, 56,16,"Guideline 56 m2 (7x8), not 49"),
    ("hs_director","Director's office + secretary",20,1,"8.3(2)",42,1, 42,1, "Guideline 42 m2 (6x7)"),
    ("hs_vicedir","Vice-director and team leader",25,1,"8.3(3)",24,1,  25,1, ""),
    ("hs_adminfin","Administration and finance",None,0,"8.3(4)",24,1,  24,1, "Guideline-mandated, omitted by client"),
    ("hs_dept","Departmental room",            40,2,"8.3(5)",30,4,     30,4, "Client 'pedagogy' 2 no.; guideline 4 no. at 30 m2"),
    ("hs_staff","Staff room and cafeteria",   136,1,"8.3(6)",150,1,   150,1,"Client staff 80 + cafeteria 56; guideline 150 (10x15)"),
    ("hs_matprod","Teaching-material production",None,0,"8.3(7)",56,1, 56,1, "Guideline-mandated, omitted by client"),
    ("hs_lab","Science laboratory",            56,3,"8.3(8)",198,3,   198,3,"Guideline 198 m2 (22x9) each, fully installed"),
    ("hs_hall","Multipurpose hall",          None,0,"8.3(9)",425.75,1,425.75,1,"Guideline-mandated, omitted by client"),
    ("hs_library","Library / reading room",   120,1,"8.3(10)",272,1,  272,1,"Guideline 272 m2 (16x17)"),
    ("hs_ict","ICT laboratory",                56,1,"8.3(11)",63,2,    63,2,"Guideline 2 no. at 63 m2, 30 MB"),
    ("hs_inclusive","Inclusive special class",None,0,"8.3(13)",56,1,   56,1,"Guideline-mandated, omitted by client"),
    ("hs_workshop","Workshop / production room",None,0,"8.3(14)",192,1,192,1,"Guideline-mandated, omitted by client (24x8)"),
    ("hs_exam","Examination printing and store",None,0,"8.3(15)",56,1, 56,1,"Guideline-mandated, omitted by client"),
    ("hs_records","Records and student register",None,0,"8.3(16)",32,1,32,1,"Guideline-mandated, omitted by client"),
    ("hs_toilet","Student toilet block",       10,1,"8.3(17)",20,None, 20,4,"1 pit per 25 students: 640/25 = 26 pits"),
    ("hs_handwash","Hand-washing area",         1,2,"-",None,None,      1,2,""),
    ("hs_genstore","General store",            30,1,"8.3(18)",42,1,    42,1,""),
    ("hs_girls","Girls' washroom",           None,0,"8.3(19)",32,1,    32,1,"Guideline-mandated, omitted by client"),
    ("hs_foodstore","Food store",            None,0,"8.3(20)",36,1,    36,1,"Guideline-mandated, omitted by client"),
    ("hs_dining","Student dining hall",        64,1,"8.3(21)",120,1,  120,1,"Guideline 120 m2 (8x15)"),
    ("hs_guard","Guard room",                None,0,"8.3(22)",12,1,    12,1,"Guideline-mandated, omitted by client"),
    ("hs_firstaid","First-aid room",           16,1,"-",None,None,     16,1,"Client addition"),
    ("hs_counsel","Counsellor",                12,1,"-",None,None,     12,1,"Client addition"),
    ("hs_maint","Maintenance room",            16,1,"-",None,None,     16,1,"Client addition"),
    ("hs_cleaner","Cleaners' room",             9,1,"-",None,None,      9,1,"Client '3x3=90' read as 9 m2"),
]

OUTDOOR = [
    ("od_kg_play","Kindergarten playground", 150,1,"7(3)",None,None,150,1,"Client 10x15"),
    ("od_pr_play","Primary playing ground",  500,1,"7(3)",None,None,500,1,"Client 25x20"),
    ("od_hs_play","Secondary playing ground",600,1,"7(3)",None,None,600,1,"Client 20x30 - note a FIBA court needs 32x19"),
    ("od_flag","Flag ceremony area",        None,0,"7(2)",None,None,600,1,"Art.7(2); may share a playing ground, used in rotation"),
    ("od_agri","Agricultural plot",         None,0,"7(4)",None,None,120,1,"Art.7(4); may be raised beds on a terrace"),
    ("od_green","Greenery / Gaaddisa",      None,0,"7(5)",None,None,200,1,"Art.7(5) and Art.2(12) shaded reading place"),
]

BLOCKS = [("kindergarten",KG),("primary",PRIMARY),("central_office",CENTRAL),("secondary",SECONDARY)]

def tot(rows, which):
    i_each, i_no = (2,3) if which=="client" else (7,8)
    s = 0.0
    for r in rows:
        e, n = r[i_each], r[i_no]
        if e is not None and n: s += e*n
    return s

prog = {"source":"school_space_program.docx (client) reconciled against Qajeelfama Lakk. 04/2016",
        "blocks":{}, "outdoor":[]}
for name, rows in BLOCKS:
    prog["blocks"][name] = {
        "rooms":[{"key":r[0],"label":r[1],"client_area_m2":r[2],"client_count":r[3],
                  "article":r[4],"guideline_area_m2":r[5],"guideline_count":r[6],
                  "adopt_area_m2":r[7],"adopt_count":r[8],"adopt_total_m2":round(r[7]*r[8],2),
                  "note":r[9]} for r in rows],
        "client_net_m2":round(tot(rows,"client"),2),
        "adopt_net_m2":round(tot(rows,"adopt"),2)}
prog["outdoor"] = [{"key":r[0],"label":r[1],"client_area_m2":r[2],"article":r[4],
                    "adopt_area_m2":r[7],"adopt_count":r[8],"note":r[9]} for r in OUTDOOR]

cl = sum(prog["blocks"][b]["client_net_m2"] for b,_ in BLOCKS)
ad = sum(prog["blocks"][b]["adopt_net_m2"] for b,_ in BLOCKS)
GU = 1.40
prog["totals"] = {
    "scenario_A_client_net_m2": round(cl,2),
    "scenario_A_gfa_m2": round(cl*GU,0),
    "scenario_B_compliant_net_m2": round(ad,2),
    "scenario_B_gfa_m2": round(ad*GU,0),
    "delta_net_m2": round(ad-cl,2),
    "delta_pct": round(100*(ad-cl)/cl,1),
    "gross_up_factor": GU,
    "outdoor_required_m2": sum(r[7]*r[8] for r in OUTDOOR),
}
classes = {"kindergarten":18,"primary":35,"secondary":16}
sizes   = {"kindergarten":30,"primary":50,"secondary":40}
prog["capacity"] = {k:{"classrooms":v,"class_size_art_11":sizes[k],"students":v*sizes[k]} for k,v in classes.items()}
prog["capacity"]["total_students"] = sum(v*sizes[k] for k,v in classes.items())
prog["capacity"]["total_classrooms"] = sum(classes.values())

os.makedirs("data", exist_ok=True)
json.dump(prog, open("data/program.json","w"), indent=2)

print(f"{'BLOCK':<18}{'client net':>12}{'compliant net':>15}{'delta':>10}")
for b,_ in BLOCKS:
    c=prog["blocks"][b]["client_net_m2"]; a=prog["blocks"][b]["adopt_net_m2"]
    print(f"{b:<18}{c:>12,.0f}{a:>15,.0f}{a-c:>+10,.0f}")
print(f"{'TOTAL NET':<18}{cl:>12,.0f}{ad:>15,.0f}{ad-cl:>+10,.0f}")
print(f"{'GFA @1.40':<18}{cl*GU:>12,.0f}{ad*GU:>15,.0f}{(ad-cl)*GU:>+10,.0f}")
print(f"\nclassrooms {prog['capacity']['total_classrooms']}  students {prog['capacity']['total_students']}")
print(f"outdoor required {prog['totals']['outdoor_required_m2']:,.0f} m2")
