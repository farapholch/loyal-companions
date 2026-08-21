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

# (id, visningsnamn, ras, päls, skugga, undersida, ögon, skala, biom)
RASER = [
    ("bailey", "Bailey", "Golden Retriever",
     (212, 168, 96), (176, 132, 68), (238, 214, 168), (86, 58, 34), 1.00, "forest"),
    ("shadow", "Shadow", "German Shepherd",
     (92, 68, 44), (44, 34, 26), (176, 138, 86), (60, 40, 24), 1.10, "plains"),
    ("kelda", "Kelda", "Siberian Husky",
     (188, 192, 200), (96, 102, 112), (240, 242, 246), (96, 178, 210), 1.05, "taiga"),
]


def sh(c, k):
    return tuple(min(255, int(v * k)) for v in c[:3]) + (255,)


def pals(rasid, pels, skugga, under, ogon):
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
                        "properties": {f"{NS}:tam": {"type": "int", "range": [0, 1],
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
            "minecraft:tameable": {"probability": 0.33, "tame_items": ["bone"],
                                   "tame_event": {"event": f"{NS}:on_tame", "target": "self"}},
        },
        "component_groups": {
            f"{NS}:tamed": {
                "minecraft:is_tamed": {},
                "minecraft:behavior.follow_owner": {"priority": 6, "speed_multiplier": 1.1,
                                                    "start_distance": 8, "stop_distance": 2},
                "minecraft:sittable": {},
                "minecraft:behavior.stay_while_sitting": {"priority": 5},
            },
            f"{NS}:vuxen": {"minecraft:scale": {"value": skala}},
            f"{NS}:valp": {"minecraft:scale": {"value": round(skala / 2, 3)},
                           "minecraft:is_baby": {}},
        },
        "events": {
            f"{NS}:on_tame": {"add": {"component_groups": [f"{NS}:tamed"]},
                              "set_property": {f"{NS}:tam": 1}},
            "minecraft:entity_spawned": {"add": {"component_groups": [f"{NS}:vuxen"]}},
            f"{NS}:grow_up": {"add": {"component_groups": [f"{NS}:vuxen"]},
                              "remove": {"component_groups": [f"{NS}:valp"]}},
        }}}
    json.dump(e, open(f"{BP}/entities/{rasid}.json", "w"), indent=2)


def klient(rasid):
    d = {"format_version": "1.10.0", "minecraft:client_entity": {"description": {
        "identifier": f"{NS}:{rasid}",
        "materials": {"default": "entity_alphatest"},
        "textures": {"default": f"textures/entity/{rasid}"},
        "geometry": {"default": "geometry.hund"},
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


if __name__ == "__main__":
    lang = []
    itex = {"resource_pack_name": "loyal", "texture_name": "atlas.items", "texture_data": {}}
    for rasid, namn, ras, pels, skugga, under, ogon, skala, biom in RASER:
        pals(rasid, pels, skugga, under, ogon)
        ikon(rasid, pels, skugga, under, ogon)
        entitet(rasid, namn, skala)
        klient(rasid)
        spawnregel(rasid, biom)
        itex["texture_data"][f"dc_{rasid}"] = {"textures": f"textures/items/dc_{rasid}"}
        lang += [f"entity.{NS}:{rasid}.name={namn} ({ras})",
                 f"entity.{rasid}.name={namn} ({ras})",
                 f"item.spawn_egg.entity.{NS}:{rasid}.name=Spawn {namn}"]
        print(f"  {namn:8} {ras:18} skala {skala}  biom {biom}")
    json.dump(itex, open(f"{RP}/textures/item_texture.json", "w"), indent=2)
    for pack in (BP, RP):
        for spr in ("en_US", "sv_SE"):
            open(f"{pack}/texts/{spr}.lang", "w", encoding="utf-8").write("\n".join(lang) + "\n")
    print(f"  {len(RASER)} raser, {len(lang)} språkrader")
