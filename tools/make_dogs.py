#!/usr/bin/env python3
"""Genererar hundarna: entiteter, klientdefinitioner, pälsar, spawnägg, språk.

Samma princip som Purrfect Companions: ingenting ritas eller skrivs för hand
som kan räknas fram ur en tabell. Geometrin är vakthundens, som redan är
byggd och verifierad i det andra paketet — den var vår första egna
fyrbenta modell och behöver inte uppfinnas igen.

Raserna nedan är PLATSHÅLLARE för den publika varianten. Familjeversionen
byter namn och pälsar mot riktiga hundar, precis som katterna gör via
variants.private.json.

    python3 tools/make_dogs.py
"""
import json, math, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/opt/purrfect-companions")
import render_regression as rr          # PNG-läsning/-skrivning och renderaren

BP = f"{BASE}/LoyalCompanions_BP"
RP = f"{BASE}/LoyalCompanions_RP"
NS = "hund"

# LUDDET. Vakthundens modell är en storvuxen vakthund: rak svans, slät hals.
# En pomeranian är motsatsen — liten, yvig krage och en svans som ligger uppe
# över ryggen. Med bara nedskalning blir hon en vargvalp, inte en pom. Därför
# får luddiga raser en EGEN geometri: samma ben och samma UV som grundmodellen,
# plus två kuber. De ligger på ledig texturyta (y 44 och nedåt, som inget annat
# använder) och målas direkt i pälsfunktionen.
# MÅTTEN ÄR TAGNA MOT KROPPEN, inte fritt valda. Kroppen är x -3.5..3.5,
# y 7..14, z -6..6. Första försöket la svansen på y 15-18, z 4-9 — den svävade
# synligt bakom hunden, för den rörde varken rygg eller bakdel. Nu överlappar
# båda kuberna kroppen med ett par enheter, vilket är hur en päls sitter.
LUDD_KUBER = [
    ("body", [-4.5, 7, -6.5], [9, 7.5, 5], [28, 44], "krage"),    # halskrage fram
    ("tail", [-1.5, 12.5, 2.5], [3, 4, 5], [0, 52], "svans"),     # yvig svans över ryggen
]


def geometri_ludd():
    """geometry.hund_ludd — grundmodellen plus krage och yvig svans."""
    g = json.load(open(f"{RP}/models/entity/hund.geo.json"))
    bas = g["minecraft:geometry"][0]
    ny = json.loads(json.dumps(bas))
    ny["description"] = dict(bas["description"], identifier="geometry.hund_ludd")
    # svansen ersätts, kragen läggs till — annars sticker den raka svansen ut
    # genom den yviga
    for b in ny["bones"]:
        if b["name"] == "tail":
            b["cubes"] = []
    for benamn, origin, size, uv, _vad in LUDD_KUBER:
        for b in ny["bones"]:
            if b["name"] == benamn:
                b.setdefault("cubes", []).append({"origin": origin, "size": size, "uv": uv})
    g["minecraft:geometry"] = [bas, ny]
    json.dump(g, open(f"{RP}/models/entity/hund.geo.json", "w"), indent=2)


# (id, visningsnamn, ras, päls, skugga, undersida, ögon, skala, biom, ludd)
# Det hunden går och hämtar. Bollen är vår egen, pinnen och benet finns i
# spelet — kastar man en pinne åt en hund ska det bara fungera.
APPORTBARA = [f"{NS}:boll", "minecraft:stick", "minecraft:bone"]
RACKVIDD = 16          # hur långt hunden letar efter något att hämta

RASER = [
    # KVARTETTEN ÄR VALD PÅ KONTRAST, inte på vilka raser som är populärast.
    # Fyra hundar som ska gå att skilja åt på en halv sekund kräver spridning i
    # tre saker samtidigt: storlek, färg och siluett. Samma insikt som
    # kattpaketets logga gav — det är kontrasten som gör att man ser VAD något
    # är, inte detaljerna.
    #
    #   Truffle  liten, mörk, luddig      (familjens Truffle)
    #   Rufus    stor, varmt guld, slät
    #   Kelda    mellan, silvergrå, blå ögon
    #   Pepper   mellan, svart med vit bringa
    #
    # (id, namn, ras, päls, skugga, undersida, ögon, skala, biom, ludd)
    ("truffle", "Truffle", "Pomeranian",
     (74, 54, 42), (44, 32, 26), (156, 114, 74), (206, 150, 70), 0.68, "plains", True),
    ("rufus", "Rufus", "Golden Retriever",
     (214, 166, 92), (172, 126, 62), (240, 216, 170), (92, 62, 36), 1.05, "forest", False),
    ("kelda", "Kelda", "Siberian Husky",
     (176, 182, 192), (88, 96, 108), (242, 244, 248), (96, 178, 210), 1.00, "taiga", False),
    ("pepper", "Pepper", "Border Collie",
     (44, 42, 46), (26, 24, 28), (238, 238, 234), (118, 84, 48), 0.95, "plains", False),
]



def sh(c, k):
    return tuple(min(255, int(v * k)) for v in c[:3]) + (255,)


def pals(rasid, pels, skugga, under, ogon, ludd=False):
    """Pälsen målas ur vakthundens UV-layout: samma kuber, andra färger.

    Vakthundens egen textur ritades kub för kub i det andra paketet; här
    läses den som MALL och färgläggs om, så alla raser garanterat delar
    exakt samma utfällning som geometrin förväntar sig."""
    w, h, px = rr.read_png("/opt/purrfect-companions/PurrfectCompanions_RP/textures/entity/hund.png")
    VAKT = {(86, 88, 96): pels, (58, 60, 68): skugga, (176, 178, 188): under,
            (232, 176, 64): ogon, (26, 26, 30): (22, 20, 20)}
    ut = []
    for rad in px:
        ny = []
        for p in rad:
            if len(p) > 3 and p[3] == 0:
                ny.append((0, 0, 0, 0)); continue
            grund = (p[0], p[1], p[2])
            traff = None
            for kalla, mal in VAKT.items():
                # tonerna i mallen är skuggade varianter av fem grundfärger;
                # närmaste grundfärg avgör, så ljus/mörk-nyanserna följer med
                d = sum((grund[i] - kalla[i]) ** 2 for i in range(3))
                if traff is None or d < traff[0]:
                    traff = (d, kalla, mal)
            _, kalla, mal = traff
            k = (sum(grund) + 1) / (sum(kalla) + 1)
            ny.append(sh(mal, k))
        ut.append(ny)
    if ludd:
        # kragen och svansen har ingen förlaga i vakthundens textur — de målas
        # här, på ytor grundmodellen inte rör
        for _b, size, uv in [(k[0], k[2], k[3]) for k in LUDD_KUBER]:
            bw, bh, bd = size
            fw, fh = math.ceil(2 * (bd + bw)), math.ceil(bd + bh)
            for y in range(uv[1], min(h, uv[1] + fh)):
                for x in range(uv[0], min(w, uv[0] + fw)):
                    ljus = 1.16 if y < uv[1] + math.ceil(bd) else (
                        0.72 if y == uv[1] + fh - 1 else 1.0)
                    ut[y][x] = sh(pels, ljus)
    rr.write_png(f"{RP}/textures/entity/{rasid}.png", w, h, ut)


def ikon(rasid, pels, skugga, under, ogon):
    """16x16 hundansikte — samma formspråk som kattpaketets spawnägg."""
    N = 16
    px = [[(0, 0, 0, 0)] * N for _ in range(N)]

    def rect(x0, y0, w, h, c):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if 0 <= x < N and 0 <= y < N:
                    px[y][x] = c
    rect(3, 3, 10, 11, pels + (255,))
    rect(2, 1, 3, 5, skugga + (255,))          # hängöron, längre än kattens
    rect(11, 1, 3, 5, skugga + (255,))
    rect(3, 3, 10, 1, sh(pels, 1.16))
    rect(5, 7, 6, 5, under + (255,))           # nosparti
    rect(6, 10, 4, 2, (22, 20, 20, 255))
    rect(5, 6, 2, 2, ogon + (255,))
    rect(9, 6, 2, 2, ogon + (255,))
    rect(3, 13, 10, 1, sh(pels, 0.7))
    rr.write_png(f"{RP}/textures/items/dc_{rasid}.png", N, N, px)


def entitet(rasid, namn, skala):
    e = {"format_version": "1.20.50", "minecraft:entity": {
        "description": {"identifier": f"{NS}:{rasid}", "is_spawnable": True,
                        "is_summonable": True, "is_experimental": False,
                        "properties": {
                            f"{NS}:tam": {"type": "int", "range": [0, 1],
                                          "default": 0, "client_sync": True},
                            # LÄGET: 0 följer, 1 stannar, 2 vaktar. Egen egenskap
                            # i stället för skriptminne — då överlever det
                            # världsomstart, och kommandot syns i selektorer så
                            # testet kan läsa tillbaka det.
                            f"{NS}:lage": {"type": "int", "range": [0, 2],
                                           "default": 0, "client_sync": True},
                            f"{NS}:bar": {"type": "int", "range": [0, 1],
                                          "default": 0, "client_sync": True}}},
        "components": {
            "minecraft:type_family": {"family": ["dc_hund", "mob"]},
            "minecraft:health": {"value": 20, "max": 20},
            "minecraft:collision_box": {"width": 0.7, "height": 0.9},
            "minecraft:physics": {}, "minecraft:pushable": {"is_pushable": True},
            "minecraft:movement": {"value": 0.33},
            "minecraft:movement.basic": {}, "minecraft:jump.static": {},
            "minecraft:navigation.walk": {"can_path_over_water": True, "avoid_water": True},
            "minecraft:nameable": {}, "minecraft:persistent": {},
            "minecraft:behavior.float": {"priority": 0},
            "minecraft:behavior.panic": {"priority": 1, "speed_multiplier": 1.4},
            "minecraft:behavior.look_at_player": {"priority": 8, "look_distance": 8},
            "minecraft:behavior.random_look_around": {"priority": 9},
            # TÄMJNING MED BEN, inte fisk. 0.33 per försök: några ben, inte ett
            # — att tämja ska kosta något, som hos katterna.
            # INGEN minecraft:equippable. Den satt här först, i tron att
            # pickup_items behövde någonstans att lägga bytet. Den registreras
            # inte ens: skriptet ser ingen equippable-komponent på hunden, och
            # vanilla FÖRSTÖR föremålet när moben når fram (även med
            # minecraft:inventory monterad — den platsen förblev tom). Därför
            # äger skriptet bärandet: det plockar bort bollen strax innan
            # vanilla hinner, och sätter hund:bar. Vaniljas enda uppgift är att
            # gå dit.
            # SHAREABLES ÄR NYCKELN TILL APPORTEN, och den kostade sex
            # serverkörningar att hitta. minecraft:behavior.pickup_items ensam
            # gör INGENTING: hunden fick beteendet, gruppen lades till, och den
            # gick ändå aldrig fram till bollen — i alla varianter vi provade
            # (i grupp, i baskomponenterna, med och utan equippable, tämjd och
            # otämjd). Räven i samma värld tog samma boll varje gång. Skillnaden
            # var den här komponenten: den är mobens ÖNSKELISTA, och utan den
            # finns det inget föremål som är värt att gå till.
            "minecraft:shareables": {"all_items": False, "items": [
                {"item": i, "want_amount": 1, "surplus_amount": 1, "priority": 0}
                for i in APPORTBARA]},
            "minecraft:tameable": {"probability": 0.33, "tame_items": ["bone"],
                                   "tame_event": {"event": f"{NS}:on_tame", "target": "self"}},
        },
        "component_groups": {
            f"{NS}:tamed": {
                "minecraft:is_tamed": {},
                "minecraft:sittable": {},
                "minecraft:behavior.stay_while_sitting": {"priority": 5},
                # KOMMANDOT GES MED ETT BEN I HANDEN. Interaktioner i
                # entitets-JSON är beprövade (kattpaketets tjugo plagg går den
                # vägen); skriptets interaktionshändelse visade sig otillförlitlig
                # i testmiljön, så den lutar vi oss inte mot här.
                "minecraft:interact": {"interactions": [{
                    "on_interact": {"filters": {"all_of": [
                        {"test": "is_family", "subject": "other", "value": "player"},
                        {"test": "is_owner", "subject": "other"},
                        {"test": "has_equipment", "domain": "hand", "subject": "other",
                         "value": "bone"}]},
                        "event": f"{NS}:nasta_lage", "target": "self"},
                    "play_sounds": "beacon.power",
                    "interact_text": "action.interact.command"}]},
            },
            f"{NS}:foljer": {
                "minecraft:behavior.follow_owner": {"priority": 6, "speed_multiplier": 1.15,
                                                    "start_distance": 8, "stop_distance": 2},
                "minecraft:behavior.random_stroll": {"priority": 12, "speed_multiplier": 0.8},
            },
            # STANNAR: inga förflyttningsbeteenden alls kvar utom panik. Hunden
            # står kvar där du lämnade den, vilket är hela poängen med ett
            # stannakommando — den ska INTE följa efter när du går.
            f"{NS}:stannar": {},
            f"{NS}:vaktar": {
                "minecraft:behavior.follow_owner": {"priority": 8, "speed_multiplier": 1.0,
                                                    "start_distance": 14, "stop_distance": 6},
                "minecraft:behavior.owner_hurt_by_target": {"priority": 2},
                "minecraft:behavior.owner_hurt_target": {"priority": 3},
                "minecraft:behavior.nearest_attackable_target": {
                    "priority": 4, "must_see": True, "reselect_targets": True,
                    "within_radius": 12,
                    "entity_types": [{"filters": {"any_of": [
                        {"test": "is_family", "subject": "other", "value": "monster"}]},
                        "max_dist": 12}]},
                "minecraft:behavior.melee_attack": {"priority": 5},
                "minecraft:attack": {"damage": 4},
            },
            # APPORT: vaniljas egen upplockning gör navigeringen åt oss. Att
            # skriptstyra en entitet fram till ett föremål går inte — det finns
            # ingen väg att sätta ett mål från skript — men pickup_items får
            # hunden att gå dit själv.
            f"{NS}:apporterar": {
                # INGEN follow_owner HÄR. Den finns redan i hund:foljer med
                # prioritet 6; två follow_owner samtidigt är två mål som slåss
                # om samma hund. Upplockningen har lägre siffra och vinner
                # därför över hemgåendet så länge bollen ligger kvar.
                "minecraft:behavior.pickup_items": {
                    "priority": 2, "max_dist": RACKVIDD, "goal_radius": 1.6,
                    "speed_multiplier": 1.3, "pickup_based_on_chance": False,
                    "track_target": True},
            },
            f"{NS}:vuxen": {"minecraft:scale": {"value": skala}},
            f"{NS}:valp": {"minecraft:scale": {"value": round(skala / 2, 3)},
                           "minecraft:is_baby": {}},
        },
        "events": {
            f"{NS}:on_tame": {"add": {"component_groups": [f"{NS}:tamed", f"{NS}:foljer"]},
                              "set_property": {f"{NS}:tam": 1}},
            # LÄGESVÄXLINGEN som en sekvens: villkoren läses uppifrån, så
            # ordningen 2->0 före 1->2 före 0->1 hindrar att ett tryck faller
            # rakt igenom alla tre steg i samma anrop.
            f"{NS}:nasta_lage": {"sequence": [
                {"filters": {"test": "int_property", "domain": f"{NS}:lage", "value": 2},
                 "set_property": {f"{NS}:lage": 0},
                 "add": {"component_groups": [f"{NS}:foljer"]},
                 "remove": {"component_groups": [f"{NS}:stannar", f"{NS}:vaktar"]}},
                {"filters": {"test": "int_property", "domain": f"{NS}:lage", "value": 1},
                 "set_property": {f"{NS}:lage": 2},
                 "add": {"component_groups": [f"{NS}:vaktar"]},
                 "remove": {"component_groups": [f"{NS}:foljer", f"{NS}:stannar"]}},
                {"filters": {"test": "int_property", "domain": f"{NS}:lage", "value": 0},
                 "set_property": {f"{NS}:lage": 1},
                 "add": {"component_groups": [f"{NS}:stannar"]},
                 "remove": {"component_groups": [f"{NS}:foljer", f"{NS}:vaktar"]}}]},
            f"{NS}:apport_pa": {"add": {"component_groups": [f"{NS}:apporterar"]}},
            f"{NS}:apport_av": {"remove": {"component_groups": [f"{NS}:apporterar"]}},
            "minecraft:entity_spawned": {"add": {"component_groups": [f"{NS}:vuxen"]}},
            f"{NS}:grow_up": {"add": {"component_groups": [f"{NS}:vuxen"]},
                              "remove": {"component_groups": [f"{NS}:valp"]}},
        }}}
    json.dump(e, open(f"{BP}/entities/{rasid}.json", "w"), indent=2)


def klient(rasid, ludd=False):
    d = {"format_version": "1.10.0", "minecraft:client_entity": {"description": {
        "identifier": f"{NS}:{rasid}",
        "materials": {"default": "entity_alphatest"},
        "textures": {"default": f"textures/entity/{rasid}"},
        "geometry": {"default": "geometry.hund_ludd" if ludd else "geometry.hund"},
        # Bennamnen i geometry.hund är head/body/leg0-3/tail — samma som
        # vaniljas fyrfotingsanimationer förväntar sig.
        "animations": {"walk": "animation.quadruped.walk",
                       "look_at_target": "animation.common.look_at_target"},
        "scripts": {"animate": [{"walk": "query.modified_move_speed"}, "look_at_target"]},
        "render_controllers": ["controller.render.default"],
        "spawn_egg": {"texture": f"dc_{rasid}", "texture_index": 0}}}}
    json.dump(d, open(f"{RP}/entity/{rasid}.json", "w"), indent=2)


def spawnregel(rasid, biom):
    json.dump({"format_version": "1.8.0", "minecraft:spawn_rules": {
        "description": {"identifier": f"{NS}:{rasid}", "population_control": "animal"},
        "conditions": [{"minecraft:spawns_on_surface": {},
                        "minecraft:brightness_filter": {"min": 7, "max": 15,
                                                        "adjust_for_weather": False},
                        "minecraft:difficulty_filter": {"min": "easy", "max": "hard"},
                        "minecraft:weight": {"default": 3},
                        "minecraft:herd": {"min_size": 1, "max_size": 2},
                        "minecraft:biome_filter": {"test": "has_biome_tag",
                                                   "operator": "==", "value": biom}}]}},
        open(f"{BP}/spawn_rules/{rasid}.json", "w"), indent=2)


def bollen():
    """Apportbollen: föremålet man kastar, plus dess recept och ikon.

    Ull och slem — mjukt och studsigt, och båda finns tidigt i ett spel. Att
    den är ett EGET föremål (och inte bara en pinne) gör att skriptet kan
    skilja "kastad boll" från allt annat som ligger på marken; hunden ska
    hämta bollen, inte spelarens tappade diamanter."""
    json.dump({"format_version": "1.20.50", "minecraft:item": {
        "description": {"identifier": f"{NS}:boll", "menu_category": {"category": "equipment"}},
        "components": {"minecraft:icon": {"texture": "dc_boll"},
                       "minecraft:display_name": {"value": "Fetch Ball"},
                       "minecraft:max_stack_size": 1}}},
        open(f"{BP}/items/boll.json", "w"), indent=2)
    json.dump({"format_version": "1.20.10", "minecraft:recipe_shaped": {
        "description": {"identifier": f"{NS}:boll"},
        "tags": ["crafting_table"],
        "pattern": [" W ", "WSW", " W "],
        "key": {"W": {"item": "minecraft:white_wool"}, "S": {"item": "minecraft:slime_ball"}},
        "unlock": [{"item": "minecraft:slime_ball"}],
        "result": {"item": f"{NS}:boll"}}},
        open(f"{BP}/recipes/boll.json", "w"), indent=2)
    N = 16
    px = [[(0, 0, 0, 0)] * N for _ in range(N)]
    for y in range(N):
        for x in range(N):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
            if d < 6.4:
                ljus = 1.0 - d / 16
                px[y][x] = (int(196 + 50 * ljus), int(72 + 40 * ljus), int(72 + 30 * ljus), 255)
            elif d < 7.2:
                px[y][x] = (120, 40, 40, 255)
    for x in range(4, 12):                      # söm, så den läser som en boll
        px[7][x] = (240, 220, 210, 255)
    rr.write_png(f"{RP}/textures/items/dc_boll.png", N, N, px)


if __name__ == "__main__":
    lang = []
    itex = {"resource_pack_name": "loyal", "texture_name": "atlas.items", "texture_data": {}}
    geometri_ludd()
    for rasid, namn, ras, pels, skugga, under, ogon, skala, biom, ludd in RASER:
        pals(rasid, pels, skugga, under, ogon, ludd)
        ikon(rasid, pels, skugga, under, ogon)
        entitet(rasid, namn, skala)
        klient(rasid, ludd)
        spawnregel(rasid, biom)
        itex["texture_data"][f"dc_{rasid}"] = {"textures": f"textures/items/dc_{rasid}"}
        lang += [f"entity.{NS}:{rasid}.name={namn} ({ras})",
                 f"entity.{rasid}.name={namn} ({ras})",
                 f"item.spawn_egg.entity.{NS}:{rasid}.name=Spawn {namn}"]
        print(f"  {namn:8} {ras:18} skala {skala}  biom {biom}{'  (ludd)' if ludd else ''}")
    bollen()
    itex["texture_data"]["dc_boll"] = {"textures": "textures/items/dc_boll"}
    lang += [f"item.{NS}:boll.name=Fetch Ball", "action.interact.command=Command",
             # SKRIPTETS KVITTON hör hemma i tabellen, inte i skriptet. Lades de
             # till i .lang-filen för hand försvann de nästa gång generatorn kördes,
             # för den skriver om filen från grunden.
             f"{NS}.apport.klar=Your dog brings the ball back.",
             f"{NS}.lage.0=Follow", f"{NS}.lage.1=Stay", f"{NS}.lage.2=Guard"]
    json.dump(itex, open(f"{RP}/textures/item_texture.json", "w"), indent=2)
    for pack in (BP, RP):
        for spr in ("en_US", "sv_SE"):
            open(f"{pack}/texts/{spr}.lang", "w", encoding="utf-8").write("\n".join(lang) + "\n")
    print(f"  {len(RASER)} raser, {len(lang)} språkrader")
