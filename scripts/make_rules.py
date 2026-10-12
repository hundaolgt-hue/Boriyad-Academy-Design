#!/usr/bin/env python3
"""Emit data/program_rules.json — the editable rule set from which the whole
schedule of accommodation is generated for ANY enrolment.

Every room carries an area (client and guideline-compliant variants) and a
COUNT RULE saying how its quantity scales. Nothing is hard-coded to the
current 2,930 students.

Count rules
  {"per":"school"}                    one per school, whatever the size
  {"per":"classroom"}                 one per classroom
  {"per":"classrooms","each":6}       one per 6 classrooms, rounded up
  {"per":"students","each":875}       one per 875 students, rounded up
  {"per":"unit"}                      one per registered unit (Art. 11 sizes);
                                      collapses to one when consolidate=true,
                                      unless consolidates=false
  {"per":"pits"}                      Art. 8.2(13)/8.3(17): one pit per
                                      pit_ratio students, pits_per_block per
                                      sanitary block
  "n" multiplies any of the above (default 1)
"""
import json, os

# key, label, article, area_client, area_compliant, count-rule, consolidates, note
KG = [
 ("classroom","Classroom","8.1(1)",49,63,{"per":"classroom"},None,
  "Art. 8.1(1) is 63 m2 (7x9); the client programme uses 49 m2 (7x7)"),
 ("golee","Golee learning commons","17(1)",0,60,{"per":"classrooms","each":6},None,
  "Art. 17(1) five learning corners, pooled per cluster. Compliant schedule only"),
 ("director","Director's office","8.1(2)",20,20,{"per":"unit"},False,
  "Art. 15 position: directors' offices duplicate per registered unit, the rest consolidate"),
 ("vice_director","Vice-director / team leader","-",20,20,{"per":"school"},None,"Client addition"),
 ("staff_room","Staff room","8.1(3)",56,72,{"per":"unit"},True,""),
 ("food_store","Food store","8.1(4)",0,36,{"per":"unit"},True,"Omitted by the client programme"),
 ("sick_bay","Sick bay / rest room","8.1(5)",12,20,{"per":"unit","n":2},True,""),
 ("dining","Children's dining","8.1(6)",20,20,{"per":"students","each":135},None,
  "Art. 8.1(6) gives 4 rooms of 20 m2 per 150-child unit = one per 37.5 children; "
  "relaxed to one per 135 on the assumption of four sittings"),
 ("toilet","Toilet block, segregated","8.1(7)",12,12,{"per":"pits"},None,
  "Adjacent handwashing required"),
 ("guard","Guard room","8.1(8)",0,9,{"per":"unit"},True,"Omitted by the client programme"),
 ("montessori","Montessori / pedagogy room","-",20,20,{"per":"unit"},True,"Client addition"),
 ("tv_room","TV room","-",56,56,{"per":"unit"},True,"Client addition"),
 ("nap_room","Nap room","-",49,49,{"per":"students","each":540},None,"Client addition"),
 ("meeting_hall","Meeting hall","-",100,100,{"per":"school"},None,"Client addition"),
 ("store","Store room","-",16,16,{"per":"school"},None,""),
 ("shower","Shower","-",1.5,1.5,{"per":"students","each":270},None,""),
 ("record_room","Record and photocopy room","-",36,36,{"per":"school"},None,""),
]

PRIMARY = [
 ("classroom","Learning classroom","8.2(1)",49,56,{"per":"classroom"},None,
  "Art. 8.2(1) is 56 m2 (7x8); the client programme uses 49 m2 (7x7)"),
 ("director","Director's office","8.2(2)",20,24,{"per":"unit"},False,""),
 ("deputy","Deputy director's office","8.2(3)",20,24,{"per":"unit","n":2},True,""),
 ("secretary","Secretary office","-",12,12,{"per":"school"},None,"Client addition"),
 ("staff_room","Staff room","8.2(5)",80,120,{"per":"unit"},True,""),
 ("staff_cafeteria","Staff cafeteria","8.2(5)",56,56,{"per":"unit"},True,
  "The client splits the cafeteria from the staff room"),
 ("dept_room","Departmental room","8.2(6)",30,24,{"per":"school","n":4},None,
  "Art. 8.2(6) reads 'bal'inni waliigalaa isaanii' - 96 m2 COMBINED for four rooms. "
  "Confirm with the Bureau; it swings 288 m2"),
 ("library","Library / reading room","8.2(4)",100,180,{"per":"unit"},True,""),
 ("env_kit","Environmental science kit room, G1-6","8.2(11)",42,64,{"per":"unit"},True,""),
 ("science_lab","General science laboratory, G7-8","8.2(12)",0,64,{"per":"unit"},True,
  "Omitted by the client programme"),
 ("ict","ICT laboratory","8.2(20)",56,63,{"per":"unit"},True,"40 computers, 20 MB link"),
 ("dining","Student dining hall","8.2(16)",80,120,{"per":"students","each":875},None,
  "Assumes staggered sittings"),
 ("general_store","General store","8.2(17)",30,36,{"per":"school"},None,""),
 ("food_store","Food store","8.2(15)",0,42,{"per":"school"},None,"Omitted by the client programme"),
 ("meeting_hall","Meeting room / hall","-",100,100,{"per":"school"},None,"Client addition"),
 ("nurse","Nurse / first-aid room","-",12,12,{"per":"school"},None,""),
 ("handwash","Hand-washing area","8.2(13)",1,2,{"per":"pits"},None,"One per sanitary block"),
 ("toilet","Student toilet block","8.2(13)",20,20,{"per":"pits"},None,
  "One pit per 25 students, 1.08 m2 per pit"),
 ("guard","Guard room","8.2(21)",4,9,{"per":"school","n":2},None,""),
 ("cleaner","Cleaners' room","-",4,4,{"per":"school"},None,""),
 ("staff_toilet","Staff toilet","-",6,6,{"per":"unit","n":2},True,""),
 ("day_care","Day care room","8.2(7)",0,32,{"per":"school"},None,"Omitted by the client programme"),
 ("exam_print","Examination printing and store","8.2(8)",0,56,{"per":"school"},None,
  "Omitted by the client programme"),
 ("records","Records and student register","8.2(9)",0,35,{"per":"school"},None,
  "Omitted by the client programme"),
 ("mat_prod","Teaching-material production","8.2(10)",0,56,{"per":"school"},None,
  "Omitted by the client programme"),
 ("girls_hygiene","Girls' hygiene room","8.2(14)",0,23.31,{"per":"unit","n":2},True,
  "Omitted by the client programme"),
 ("sen_centre","Special-needs support centre","8.2(18)",0,72,{"per":"unit","n":2},True,
  "Omitted by the client programme"),
 ("inclusive","Inclusive special class","8.2(19)",0,56,{"per":"school"},None,
  "Omitted by the client programme"),
]

SECONDARY = [
 ("classroom","Classroom","8.3(1)",49,56,{"per":"classroom"},None,
  "Art. 8.3(1) is 56 m2 (7x8); the client programme uses 49 m2 (7x7)"),
 ("director","Director's office with secretary","8.3(2)",20,42,{"per":"unit"},False,""),
 ("vice_director","Vice-director and team leader","8.3(3)",25,25,{"per":"unit"},True,""),
 ("admin_finance","Administration and finance","8.3(4)",0,24,{"per":"school"},None,
  "Omitted by the client programme"),
 ("dept_room","Departmental room","8.3(5)",40,30,{"per":"school","n":4},None,
  "Art. 8.3(5): 120 m2 total, 30 m2 each"),
 ("staff_room","Staff room and cafeteria","8.3(6)",136,150,{"per":"unit"},True,""),
 ("mat_prod","Teaching-material production","8.3(7)",0,56,{"per":"school"},None,
  "Omitted by the client programme"),
 ("science_lab","Science laboratory","8.3(8)",56,198,{"per":"school","n":3},None,
  "Biology, chemistry and physics separately, fully installed, 22x9 m each"),
 ("hall","Multipurpose hall","8.3(9)",0,425.75,{"per":"school"},None,
  "Omitted by the client programme. 16.25 x 26.20 m - sets the minimum bar depth"),
 ("library","Library / reading room","8.3(10)",120,272,{"per":"unit"},True,"16 x 17 m"),
 ("ict","ICT laboratory","8.3(11)",56,63,{"per":"unit","n":2},True,"40 computers, 30 MB link"),
 ("inclusive","Inclusive special class","8.3(13)",0,56,{"per":"school"},None,
  "Omitted by the client programme"),
 ("workshop","Workshop / production room","8.3(14)",0,192,{"per":"school"},None,
  "Omitted by the client programme. 24 x 8 m"),
 ("exam_print","Examination printing and store","8.3(15)",0,56,{"per":"school"},None,
  "Omitted by the client programme"),
 ("records","Records and student register","8.3(16)",0,32,{"per":"school"},None,
  "Omitted by the client programme"),
 ("toilet","Student toilet block","8.3(17)",20,20,{"per":"pits"},None,
  "One pit per 25 students"),
 ("handwash","Hand-washing area","-",1,1,{"per":"pits"},None,""),
 ("general_store","General store","8.3(18)",30,42,{"per":"school"},None,""),
 ("girls_washroom","Girls' washroom","8.3(19)",0,32,{"per":"unit"},True,
  "Omitted by the client programme"),
 ("food_store","Food store","8.3(20)",0,36,{"per":"school"},None,"Omitted by the client programme"),
 ("dining","Student dining hall","8.3(21)",64,120,{"per":"students","each":640},None,
  "Assumes staggered sittings"),
 ("guard","Guard room","8.3(22)",0,12,{"per":"school"},None,"Omitted by the client programme"),
 ("first_aid","First-aid room","-",16,16,{"per":"school"},None,"Client addition"),
 ("counsellor","Counsellor","-",12,12,{"per":"school"},None,"Client addition"),
 ("maintenance","Maintenance room","-",16,16,{"per":"school"},None,"Client addition"),
 ("cleaner","Cleaners' room","-",9,9,{"per":"school"},None,
  "Client document reads '3m x 3m = 90 m2'; taken as 9 m2"),
]

CENTRAL = [
 ("managing_director","Managing director","-",30,30,{"per":"school"},None,""),
 ("principal","Principal","-",25,25,{"per":"school"},None,""),
 ("secretary","Secretary","-",12,12,{"per":"school"},None,""),
 ("academic_director","Academic director","-",20,20,{"per":"school"},None,""),
 ("quality","Quality audit and data","-",30,30,{"per":"school"},None,""),
 ("record_officer","Record officer","-",30,30,{"per":"school"},None,""),
 ("hrm_finance","HRM and finance","-",20,20,{"per":"school"},None,""),
 ("cashier","Cashier and accountant","-",12,12,{"per":"school"},None,""),
 ("toilet","Toilet","-",2,2,{"per":"school","n":2},None,""),
 ("store","Store","-",30,30,{"per":"school"},None,""),
]

def pack(rows):
    out = []
    for k, lbl, art, ac, acp, cnt, cons, note in rows:
        r = {"key": k, "label": lbl, "article": art,
             "area_m2": {"client": ac, "compliant": acp},
             "count": cnt}
        if cons is not None:
            r["consolidates"] = cons
        if note:
            r["note"] = note
        out.append(r)
    return out

RULES = {
 "_about": "Editable rule set for the Boriyad schedule of accommodation. "
           "Every quantity is derived from enrolment; nothing is fixed to a "
           "particular student number. See docs/06-rhino-parametric-model.md.",
 "governing_standard": "Qajeelfama Istaandaardii Manneen Barnootaa Oromiyaa, Lakk. 04/2016",
 "registered_unit_size": {"kindergarten": 150, "primary": 1200, "secondary": 1280,
   "_article": "Art. 11(1)-(3). Enrolment above a unit size implies another "
               "registered unit; Art. 15 lets them share a compound."},
 "class_size": {"kindergarten": 30, "primary": 50, "secondary": 40,
   "_article": "Art. 11. Overridable, but these drive the classroom count."},
 "sanitary": {"students_per_pit": 25, "pit_area_m2": 1.08, "pits_per_block": 8,
   "_article": "Art. 8.2(13), 8.3(17). Pits cannot stack above ground, so this "
               "is waterborne sanitation in practice."},
 "gross_up_factor": 1.40,
 "gross_up_composition": {"net_scheduled_rooms": 0.715, "horizontal_circulation": 0.14,
   "vertical_circulation": 0.055, "structure_and_walls": 0.065, "services": 0.025},
 "blocks": {"kindergarten": pack(KG), "primary": pack(PRIMARY),
            "secondary": pack(SECONDARY), "central_office": pack(CENTRAL)},
}

os.makedirs("data", exist_ok=True)
json.dump(RULES, open("data/program_rules.json", "w"), indent=2)
n = sum(len(v) for v in RULES["blocks"].values())
print(f"wrote data/program_rules.json — {n} room rules across {len(RULES['blocks'])} blocks")
