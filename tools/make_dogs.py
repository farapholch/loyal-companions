#!/usr/bin/env python3
"""Genererar hundarna: geometrier, pälsar, entiteter, klientdefinitioner,
spawnägg, spawnregler, renderarkontroller och språkfiler.

Ingenting ritas eller skrivs för hand som kan räknas fram ur en tabell.

DET SOM GÖR ATT MAN SER SKILLNAD PÅ HUNDARNA ÄR SILUETTEN, inte färgen. Första
uppsättningen var fyra omfärgade kopior av samma vakthundsmodell, och på håll
såg de likadana ut. Nu byggs kroppen ur mått (benhöjd, kroppslängd,
huvudstorlek, öronform), så en tax är låg och lång, en bernhardshund är tung
och en pomeranian är liten och yvig — och pälsmönstren (fläckar, sadel,
bringa, strumpor, mask, bläs) målas ovanpå.

UV-YTAN PACKAS AUTOMATISKT. Handplockade texturkoordinater höll så länge
modellen var en enda, men med sex kroppsvarianter blev det en karta att hålla
i huvudet, och två kuber som delar yta ger en textur där benen bär ansiktet.

    python3 tools/make_dogs.py
"""
import json, math, os, sys
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/opt/purrfect-companions")
import render_regression as rr          # PNG-läsning/-skrivning

BP = f"{BASE}/LoyalCompanions_BP"
RP = f"{BASE}/LoyalCompanions_RP"
NS = "hund"
TW = TH = 128                          # texturduk; 64 räckte inte till sex kroppar

# Det hunden går och hämtar. Bollen är vår egen, pinnen och benet finns i
# spelet — kastar man en pinne åt en hund ska det bara fungera.
APPORTBARA = [f"{NS}:boll", "minecraft:stick", "minecraft:bone"]
RACKVIDD = 16          # hur långt hunden letar efter något att hämta


# --- kroppen -----------------------------------------------------------------
# Måtten är i modellenheter (16 = ett block). Allt hänger ihop: huvudet sitter
# framför kroppen, nosen framför huvudet, svansen bakom. Ändras kroppslängden
# följer huvudet med, och det är hela poängen med att räkna fram kuberna i
# stället för att skriva av dem.
def kroppsdelar(bh=6, kl=13, kb=7, kh=5.5, hs=6.5, oron="upp", ludd=False):
    """bh benhöjd, kl kroppslängd, kb kroppsbredd, kh kroppshöjd, hs huvudstorlek.

    PROPORTIONERNA ÄR RÄTTADE MOT SPELET, inte mot en trekvartsrendering. Rakt
    framifrån — vyn man möter när en hund springer emot en — såg de första
    måtten ut som en stående figur: kroppens framsida var 7 bred och 7 hög och
    stod på 7 enheter ben, alltså en smal pelare på fjorton enheter. Nu är
    kroppen lägre (5,5), benen kortare (6) och huvudet större (6,5), och det
    sitter NER I BRINGAN i stället för ovanpå ryggen."""
    hz = -kl / 2 - 3                                  # huvudets framkant i z
    # Huvudets underkant låg på bh+4, alltid tre enheter ovanför ryggen — det
    # gav en liten låda som balanserade på en stor. Nu överlappar det bålen.
    hy = bh + kh - 3
    # NOSPARTIET VAR NÄSTAN LIKA BRETT SOM HUVUDET (hs-2 av hs) och nästan lika
    # högt, så ansiktet framifrån blev en ram runt en platta — och med en stor
    # svart nos mitt i läste det som en skärm, inte som ett djur. Smalare och
    # lägre nos ger plats åt ögonen ovanför.
    nb = hs - 3                                       # nosens bredd
    nh = hs * 0.45                                    # nosens höjd
    d = [
        ("body", "body", None, [-kb / 2, bh, -kl / 2], [kb, kh, kl]),
        ("head", "head", None, [-hs / 2, hy, hz], [hs, hs, 5]),
        ("nos", "head", None, [-nb / 2, hy + 0.5, hz - 3], [nb, nh, 3]),
    ]
    # ÖRONEN MÅSTE SYNAS. Första försöket gav hängöron en enhets tjocklek i
    # samma färg som huvudet, och i renderingen fanns de helt enkelt inte —
    # golden retrievern såg ut som en varg. De sticker nu UT från huvudet, är
    # två enheter tjocka och målas i skuggfärgen.
    if oron == "upp":
        for x in (-hs / 2, hs / 2 - 2):
            d.append(("ora", "head", None, [x, hy + hs - 0.5, hz + 1], [2, 3, 1.5]))
    else:
        # HELT UTANFÖR SKALLEN. Med öronen inskjutna en bit i huvudet las de
        # samman till ett mörkt block ovanpå — dalmatinern såg ut att ha hjälm.
        langd = 6 if oron == "lang" else 4.5
        for x in (-hs / 2 - 2, hs / 2):
            d.append(("ora", "head", None, [x, hy + hs - langd, hz + 1], [2, langd, 3]))
    bz = [-kl / 2, kl / 2 - 3]                        # fram- och bakben i z
    for i, (x, z) in enumerate([(-kb / 2, bz[0]), (kb / 2 - 3, bz[0]),
                                (-kb / 2, bz[1]), (kb / 2 - 3, bz[1])]):
        d.append(("ben", f"leg{i}", None, [x, 0, z], [3, bh, 3]))
    if ludd:
        # LUDDET. En pomeranian nedskalad från en vakthund är en vargvalp; det
        # är kragen och den yviga svansen som gör henne till en pom. Kuberna
        # ÖVERLAPPAR kroppen med ett par enheter — första försöket la svansen
        # fritt bakom hunden och den svävade synligt.
        # KRAGEN SITTER PÅ HALSEN, inte på hela bålen. Första försöket gjorde
        # den lika lång som kroppen och pomeranianen blev en brun låda med
        # huvud — det såg ut som två kroppar efter varandra.
        d.append(("krage", "body", None, [-kb / 2 - 0.75, bh + 0.5, -kl / 2 - 1], [kb + 1.5, kh - 0.5, 4]))
        d.append(("svans", "tail", None, [-1.5, bh + kh - 1, kl / 2 - 2.5], [3, 4, 4.5]))
    else:
        d.append(("svans", "tail", None, [-1, bh + kh - 2, kl / 2], [2, 6, 2]))
    # HALSBANDET: en kub per färg kring halsen, alla på samma plats. Bara den
    # som hund:halsband pekar ut visas. Åtta kuber i stället för en tintad är
    # inte elegant, men renderarkontroller kan bara tända och släcka BEN — de
    # kan inte färga ett enskilt ben, och en tint hade färgat hela hunden.
    for i, (namn, _f) in enumerate(HALSBAND, 1):
        d.append(("hals", f"hals{i}", "body", [-kb / 2 - 0.4, bh + kh - 3.5, -kl / 2 - 0.4],
                  [kb + 0.8, 2, 2.4]))
    # BOLLEN I MUNNEN: en kub per sort vid nosen, hängd i huvudbenet så den
    # följer med när hunden tittar sig omkring. Renderarkontrollern visar den
    # som hund:bar pekar ut.
    for namn in ("mun_boll", "mun_pinne", "mun_ben"):
        # UNDER KÄKEN, inte framför ansiktet. Tidigare satt en 2,5-kub i jämnhöjd
        # med nosen och nästan lika bred — Pelle läste den som "en konstig röd
        # nos", inte som en boll i munnen. Nu är den mindre än nosen och hänger
        # under käklinjen, där en hund faktiskt bär något.
        d.append((namn, namn, "head", [-1, hy - 1.25, hz - 4], [2, 2, 2]))
    return d


PIVOT = lambda bh, kl, kb, kh, hs: {
    "body": [0, bh + kh / 2, 0],
    "head": [0, bh + kh - 2, -kl / 2],     # nacken, där huvudet möter kroppen
    "leg0": [-kb / 2 + 1.5, bh, -kl / 2 + 1.5], "leg1": [kb / 2 - 1.5, bh, -kl / 2 + 1.5],
    "leg2": [-kb / 2 + 1.5, bh, kl / 2 - 1.5], "leg3": [kb / 2 - 1.5, bh, kl / 2 - 1.5],
    "tail": [0, bh + kh - 2, kl / 2],
    "mun_boll": [0, bh + kh - 2, -kl / 2], "mun_pinne": [0, bh + kh - 2, -kl / 2],
    "mun_ben": [0, bh + kh - 2, -kl / 2],
    **{f"hals{i}": [0, bh + kh / 2, -kl / 2] for i in range(1, 9)},
}

# Färgerna man kan sätta på sin hund, i den ordning hund:halsband räknar dem.
# (färgämnets id, färg)
HALSBAND = [("red", (176, 46, 38)), ("orange", (216, 122, 30)),
            ("yellow", (232, 196, 48)), ("lime", (110, 190, 46)),
            ("light_blue", (86, 166, 220)), ("blue", (52, 72, 176)),
            ("purple", (134, 66, 186)), ("pink", (230, 130, 176))]

# (namn, benhöjd, kroppslängd, kroppsbredd, kroppshöjd, huvud, öron, ludd)
KROPPAR = {
    "normal":  (6, 13, 7, 5.5, 6.5, "upp", False),
    "hang":    (6, 13, 7, 5.5, 6.5, "hang", False),
    "ludd":    (6, 12, 7, 5.5, 6.5, "upp", True),
    "kort":    (3, 16, 7, 5, 5.5, "lang", False),     # tax: låg, lång, långa öron
    "tung":    (7, 14, 8, 6.5, 7.5, "hang", False),   # bernhardshund
    "liten":   (4.5, 10, 6, 5, 5.5, "upp", False),    # terrier
}


def packa(delar):
    """Hyllpackning av UV-ytan. Kuber sorteras på höjd och läggs ut i rader.

    Bedrocks utfällning av en kub (b,h,d) är 2*(d+b) bred och d+h hög."""
    rutor = []
    for i, (_roll, _ben, _f, _o, size) in enumerate(delar):
        b, h, d = size
        rutor.append((i, math.ceil(2 * (d + b)), math.ceil(d + h)))
    x = y = radhojd = 0
    uv = {}
    for i, w, h in sorted(rutor, key=lambda r: -r[2]):
        if x + w > TW:
            x, y, radhojd = 0, y + radhojd, 0
        if y + h > TH:
            raise SystemExit(f"UV-ytan räcker inte till ({TW}x{TH})")
        uv[i] = [x, y]
        x += w
        radhojd = max(radhojd, h)
    return uv


def geometri(namn, matt):
    bh, kl, kb, kh, hs, oron, ludd = matt
    delar = kroppsdelar(bh, kl, kb, kh, hs, oron, ludd)
    uv = packa(delar)
    ben = {}
    for i, (_roll, benamn, forlder, origin, size) in enumerate(delar):
        b = ben.setdefault(benamn, {"name": benamn, "pivot": PIVOT(bh, kl, kb, kh, hs).get(
            benamn, [0, bh, 0]), "cubes": []})
        if forlder:
            b["parent"] = forlder
        b["cubes"].append({"origin": origin, "size": size, "uv": uv[i]})
    return {
        "description": {
            "identifier": f"geometry.hund_{namn}",
            # MÅSTE stämma med PNG-filen, annars läses UV i fel skala och
            # modellen blir obegriplig i spelet — servern märker ingenting.
            "texture_width": TW, "texture_height": TH,
            "visible_bounds_width": 3, "visible_bounds_height": 2.5,
            "visible_bounds_offset": [0, 0.9, 0],
        },
        "bones": list(ben.values()),
    }, delar, uv


def skriv_geometrier():
    g, delar, uv = {}, {}, {}
    for namn, matt in KROPPAR.items():
        g[namn], delar[namn], uv[namn] = geometri(namn, matt)
    json.dump({"format_version": "1.12.0",
               "minecraft:geometry": [g[n] for n in KROPPAR]},
              open(f"{RP}/models/entity/hund.geo.json", "w"), indent=2)
    return delar, uv


def renderarkontroller():
    """Egen renderarkontroller: controller.render.default visar allt, och då
    skulle hunden alltid gå omkring med boll, pinne OCH ben i munnen."""
    json.dump({"format_version": "1.10.0", "render_controllers": {
        "controller.render.hund": {
            "geometry": "Geometry.default",
            "materials": [{"*": "Material.default"}],
            "textures": ["Texture.default"],
            "part_visibility": [
                {"*": True},
                {"mun_boll": "q.property('hund:bar') == 1"},
                {"mun_pinne": "q.property('hund:bar') == 2"},
                {"mun_ben": "q.property('hund:bar') == 3"},
                *[{f"hals{i}": f"q.property('hund:halsband') == {i}"}
                  for i in range(1, len(HALSBAND) + 1)]]}}},
        open(f"{RP}/render_controllers/hund.render_controllers.json", "w"), indent=2)


# --- pälsen ------------------------------------------------------------------
def sh(c, k):
    return tuple(min(255, int(v * k)) for v in c[:3]) + (255,)


# FYRA TEXLAR PER ENHET sedan v1.5.0, samma mekanism som kattpaketet: geometrin
# deklarerar TW x TH uv-enheter och PNG:en är SKALA gånger det; Bedrock läser
# den tätare. Innan dess var varje sida av hunden ett färgfält med en ljusare
# ovansida — bringan var en vit kil, ögat en texel, nosen en svart ruta.
SKALA = 4
sys.path.insert(0, "/opt/purrfect-companions/tools")
from make_cat_pals import Duk, korn, blanda, skala as ton, lum, _h

SIDSKUGGA = {"top": 1.06, "bottom": 0.80, "north": 1.0, "south": 0.95,
             "east": 0.95, "west": 0.95}

# Föremålen i munnen har föremålens färger, inte hundens.
MUNFARG = {"mun_boll": (196, 72, 72), "mun_pinne": (140, 102, 58),
           "mun_ben": (238, 236, 222)}


def _R(f):
    """Unit-yta -> texelrektangel."""
    return tuple(v * SKALA for v in f)


def fur(bas, sida, riktning="x", k=1.0):
    """Päls: ljus uppifrån, korn, och svaga strån längs pälsens riktning."""
    bas = tuple(bas[:3])

    def fn(a, b, x, y):
        c = ton(bas, SIDSKUGGA[sida] * (1.05 - 0.14 * b))
        stra = _h(x // 3, y, 21) if riktning == "x" else _h(x, y // 3, 21)
        if stra < 0.10:
            c = ton(c, 0.93)
        return korn(c, x, y, k)
    return fn


def flat(c):
    c = tuple(c[:3])
    return lambda a, b, x, y: korn(c, x, y, 0.5)


def pals(rasid, delar, uv, farg):
    """Målar en hel päls ur kubtabellen: en yta per kubsida, sedan mönstren,
    sist ansiktet. Att måla ur SAMMA tabell som geometrin byggs av är hela
    poängen — UV och bild kan då inte glida isär."""
    duk = Duk(TW * SKALA, TH * SKALA)
    P, SK, UN = tuple(farg["pals"]), tuple(farg["skugga"]), tuple(farg["under"])
    halsraknare = [0]

    def fyll(f, fn):
        duk.yta(_R(f), fn, 255)

    def rect(x0, y0, w, h, c):
        """Mönstrens gamla gränssnitt: en enhetsrektangel i en färg, med korn."""
        duk.yta((x0 * SKALA, y0 * SKALA, w * SKALA, h * SKALA),
                lambda a, b, x, y: korn(tuple(c[:3]), x, y, 0.6), 255)

    sidor = {}
    for i, (roll, benamn, _f, _o, size) in enumerate(delar):
        b_, h_, d_ = size
        u, v = uv[i]
        f = rr.faces(u, v, b_, h_, d_)
        sidor.setdefault(roll, []).append((f, size))
        if roll == "hals":
            grund = HALSBAND[halsraknare[0]][1]
            halsraknare[0] = (halsraknare[0] + 1) % len(HALSBAND)
            _halsband(duk, f, grund)
            continue
        if roll in MUNFARG:
            _munsak(duk, roll, f, MUNFARG[roll])
            continue
        grund = {"krage": UN, "ora": SK}.get(roll, P)
        riktning = "y" if roll in ("ben", "svans") else "x"
        k = 1.8 if roll == "krage" else 1.0
        for namn, yta in f.items():
            fyll(yta, fur(grund, namn, riktning, k))
        if roll == "ora" and size[1] <= 3.5:
            # innerörat på ett uppstående öra: ljusare, mot underfärgen
            X0, Y0, FW, FH = f["north"]
            inre = blanda(SK, UN, 0.45)
            fyll(f["north"], lambda a, b, x, y: korn(inre, x, y, 0.5)
                 if 0.2 < b < 0.9 and abs(a - 0.5) < 0.1 + 0.3 * b else fur(SK, "north")(a, b, x, y))

    for mall in farg.get("monster", []):
        MONSTER[mall](rect, sidor, farg, fyll)

    # ANSIKTET sist, så inget mönster målar över ögonen.
    mork = blanda(P, (0, 0, 0), 0.75) if lum(P) > 70 else blanda(P, (255, 255, 255), 0.35)
    for f, size in sidor["head"]:
        hs = size[0]
        fx, fy, fw, fh = f["north"]
        synliga = hs - (0.5 + hs * 0.45)
        rad = max(0, int(synliga) - 1)
        cy = rad + 0.55                                   # ögats mitt, i enheter från ytans topp
        ogon = [(1.5, cy, +1), (hs - 1.5, cy, -1)]
        rx, ry = 0.62, 0.55
        iris, iris_m = tuple(farg["ogon"]), blanda(tuple(farg["ogon"]), (0, 0, 0), 0.45)
        X0, Y0, FW, FH = _R(f["north"])

        def ansikte(a, b, x, y, fn0=fur(P, "north")):
            X, Y = a * fw, b * fh                         # i enheter
            c = fn0(a, b, x, y)
            # NOSPARTIET ljusnar nedåt mot underfärgen
            if b > 0.45 and abs(a - 0.5) < 0.36:
                c = blanda(c, UN, min(1.0, (b - 0.45) / 0.3) * 0.5)
            for ex, ey, inat in ogon:
                dx, dy = (X - ex) / rx, (Y - ey) / ry
                r = math.hypot(dx, dy)
                if r > 1.0:
                    # ögonbrynet: en mjuk skugga ovanför
                    if abs(X - ex) < rx + 0.2 and 0 < ey - ry - Y < 0.45:
                        return blanda(c, mork, 0.25)
                    continue
                if r > 0.80:
                    return mork
                if math.hypot(X - ex, Y - ey) < 0.26:
                    return blanda(iris_m, (0, 0, 0), 0.8)               # pupillen
                if math.hypot(X - (ex + inat * 0.22), Y - (ey - 0.22)) < 0.17:
                    return (255, 255, 255)                              # glansen
                return blanda(iris, iris_m, 0.15 + 0.5 * (dy + 1) / 2)
            return c
        fyll(f["north"], ansikte)

    for f, size in sidor["nos"]:
        fx, fy, fw, fh = f["north"]
        nosbas = ton(UN, 0.96)
        tipp = (26, 24, 24)
        mun = blanda(tipp, UN, 0.35)

        def nos(a, b, x, y):
            X, Y = a * fw, b * fh
            c = korn(ton(nosbas, 1.04 - 0.1 * b), x, y, 0.5)
            # NOSTIPPEN: en rundad mörk fläck överst i mitten, med näsborrar
            if math.hypot((X - fw / 2) / (fw * 0.24), (Y - 0.55) / 0.55) < 1.0:
                if abs(abs(X - fw / 2) - fw * 0.09) < 0.12 and abs(Y - 0.6) < 0.14:
                    return blanda(tipp, (255, 255, 255), 0.25)         # näsborrar
                return tipp
            # MUNNEN: streck ner från nosen och en liten båge åt varje håll
            if abs(X - fw / 2) < 0.14 and 1.05 < Y < fh * 0.72:
                return mun
            if fh * 0.62 < Y < fh * 0.62 + 0.28 and 0.3 < abs(X - fw / 2) < fw * 0.3:
                return mun
            return c
        fyll(f["north"], nos)
        fyll(f["top"], fur(ton(P, 1.06), "top"))
    rr.write_png(f"{RP}/textures/entity/{rasid}.png", TW * SKALA, TH * SKALA, duk.px)


def _halsband(duk, f, c):
    """Läderhalsband: sömmar längs kanten och ett spänne fram."""
    c = tuple(c[:3])
    stygn = blanda(c, (255, 255, 255), 0.45)
    for namn, yta in f.items():
        X0, Y0, FW, FH = _R(yta)

        def fn(a, b, x, y, namn=namn, FW=FW, FH=FH):
            X, Y = a * FW, b * FH
            col = ton(c, SIDSKUGGA[namn] * (1.05 - 0.14 * b))
            if namn in ("north", "south", "east", "west") and (1 <= Y < 2 or FH - 2 <= Y < FH - 1) and (x % 3):
                return stygn
            if namn == "north" and abs(a - 0.5) < 0.09 and 0.15 < b < 0.85:
                if abs(a - 0.5) < 0.05 and 0.3 < b < 0.7:
                    return (120, 100, 60)                         # spännets mitt
                return (214, 190, 110)                            # spännet
            return korn(col, x, y, 0.4)
        duk.yta((X0, Y0, FW, FH), fn, 255)


def _munsak(duk, roll, f, c):
    """Bollen är rund, pinnen har ådring och benet har knölar."""
    c = tuple(c[:3])
    for namn, yta in f.items():
        X0, Y0, FW, FH = _R(yta)

        def fn(a, b, x, y, namn=namn, FW=FW, FH=FH):
            X, Y = a * FW, b * FH
            if roll == "mun_boll":
                r = math.hypot(a - 0.38, b - 0.35)
                col = blanda(c, (255, 255, 255), max(0.0, 0.45 - r))
                col = blanda(col, (0, 0, 0), max(0.0, (math.hypot(a - 0.5, b - 0.5) - 0.35)) * 0.8)
                if abs((a + b * 0.4) % 1 - 0.55) < 0.04:
                    col = blanda(col, (255, 255, 255), 0.5)       # sömmen
                return col
            if roll == "mun_pinne":
                col = ton(c, 1.0 + 0.08 * math.sin(Y * 1.7))
                if _h(x // 4, y, 22) < 0.15:
                    col = ton(col, 0.8)                            # ådring
                return korn(col, x, y, 0.5)
            col = ton(c, 1.02 - 0.12 * b)                          # benet
            if (a < 0.2 or a > 0.8) and namn in ("north", "south", "top", "bottom"):
                col = ton(col, 0.88)                               # knölarna i ändarna
            if abs(b - 0.5) < 0.06 and 0.2 < a < 0.8:
                col = ton(col, 0.9)
            return korn(col, x, y, 0.3)
        duk.yta((X0, Y0, FW, FH), fn, 255)


# --- mönstren ---------------------------------------------------------------
# Alla får (rect, sidor, farg, fyll): rect målar en enhetsrektangel i en färg,
# fyll(yta, fn) målar en hel yta med en funktion av (a, b, x, y).
def m_brost(rect, sidor, farg, fyll):
    """Ljus bringa — en SMAL kil som smalnar av nedåt, med mjuk kant."""
    UN = tuple(farg["under"])
    for f, size in sidor["body"]:
        fx, fy, fw, fh = f["north"]

        def kil(a, b, x, y):
            if b < 0.42:
                return None
            halv = (0.36 - 0.22 * (b - 0.42) / 0.58) + 0.03 * math.sin(b * 25 + a * 7)
            if abs(a - 0.5) < halv:
                return korn(UN, x, y, 0.6)
            return None
        fyll(f["north"], kil)
        bx, by, bw, bh = f["bottom"]
        fyll((bx + 1, by, bw - 2, bh), lambda a, b, x, y: korn(ton(UN, 0.85), x, y, 0.6))


def m_sockor(rect, sidor, farg, fyll):
    """Vita tassar: nedre tredjedelen av varje bensida, med vågig kant."""
    UN = tuple(farg["under"])
    for f, size in sidor["ben"]:
        for namn in ("north", "south", "east", "west"):
            k = SIDSKUGGA[namn]
            fyll(f[namn], lambda a, b, x, y, k=k: korn(ton(UN, k), x, y, 0.6)
                 if b > 0.64 + 0.04 * math.sin(a * 9 + 1) else None)
        fyll(f["bottom"], lambda a, b, x, y: korn(ton(UN, 0.75), x, y, 0.6))


def m_blas(rect, sidor, farg, fyll):
    """Bläs: en ljus rand mitt i ansiktet och över nosryggen, smalare upptill."""
    UN = tuple(farg["under"])
    for f, size in sidor["head"]:
        fw = f["north"][2]
        fyll(f["north"], lambda a, b, x, y: korn(UN, x, y, 0.6)
             if abs(a - 0.5) * fw < 0.35 + 0.25 * b else None)
        fyll(f["top"], lambda a, b, x, y: korn(ton(UN, 1.05), x, y, 0.6)
             if abs(a - 0.5) * f["top"][2] < 0.5 else None)
    for f, size in sidor["nos"]:
        fyll(f["top"], lambda a, b, x, y: korn(ton(UN, 1.05), x, y, 0.6)
             if abs(a - 0.5) * f["top"][2] < 0.5 else None)


def m_mask(rect, sidor, farg, fyll):
    """Mörk mask kring ögonen med ljus bläs — huskyns kännetecken."""
    SK, UN = tuple(farg["skugga"]), tuple(farg["under"])
    for f, size in sidor["head"]:
        fh = f["north"][3]
        fyll(f["north"], lambda a, b, x, y: korn(SK, x, y, 0.6)
             if b * fh < 3.0 + 0.4 * math.sin(a * 12) else None)
        fyll(f["north"], lambda a, b, x, y: korn(UN, x, y, 0.6)
             if abs(a - 0.5) * f["north"][2] < 0.55 + 0.35 * b else None)
        for namn in ("top", "east", "west"):
            fyll(f[namn], lambda a, b, x, y, n=namn: korn(ton(SK, SIDSKUGGA[n]), x, y, 0.6)
                 if (n == "top" or b < 0.45) else None)


def m_sadel(rect, sidor, farg, fyll):
    """Sadel: mörk rygg och mörka sidor med rundad nederkant — beagle, terrier."""
    SK = tuple(farg["skugga"])
    for f, size in sidor["body"]:
        fyll(f["top"], lambda a, b, x, y: korn(ton(SK, 1.1), x, y, 0.6))
        for namn in ("east", "west", "south"):
            k = SIDSKUGGA[namn]
            fyll(f[namn], lambda a, b, x, y, k=k: korn(ton(SK, k), x, y, 0.6)
                 if b < 0.5 + 0.1 * math.sin(a * 6.5) else None)


def m_flackar(rect, sidor, farg, fyll):
    """Runda prickar över hela hunden — dalmatinern. Deterministiska, så
    samma hund får samma prickar varje körning."""
    SK = tuple(farg["skugga"])
    for roll in ("body", "head", "ben", "svans", "nos"):
        for f, size in sidor.get(roll, []):
            for namn, (fx, fy, fw, fh) in f.items():
                prickar = []
                n = int(fx * 31 + fy * 17) & 0x7FFFFFFF
                for _ in range(max(1, int(fw * fh / 7))):
                    n = (n * 1103515245 + 12345) & 0x7FFFFFFF
                    prickar.append(((n >> 7) % 1000 / 1000 * fw, (n >> 17) % 1000 / 1000 * fh,
                                    0.35 + ((n >> 3) & 3) * 0.12))
                k = SIDSKUGGA[namn]

                def fn(a, b, x, y, prickar=prickar, fw=fw, fh=fh, k=k):
                    X, Y = a * fw, b * fh
                    for px_, py_, r in prickar:
                        if math.hypot(X - px_, (Y - py_) * 1.15) < r:
                            return korn(ton(SK, k), x, y, 0.4)
                    return None
                fyll((fx, fy, fw, fh), fn)


MONSTER = {"brost": m_brost, "sockor": m_sockor, "blas": m_blas,
           "mask": m_mask, "sadel": m_sadel, "flackar": m_flackar}


# --- raserna -----------------------------------------------------------------
# Åtta hundar som ska gå att skilja åt på en halv sekund. Det kräver spridning i
# TRE saker samtidigt: storlek, färg och siluett — samma insikt som kattpaketets
# logga gav, att det är kontrasten som gör att man ser VAD något är.
#
# ...OCH DE SKA VARA OLIKA ATT ANVÄNDA. Fram till 2026-08-28 hade alla åtta
# exakt samma liv (20), fart (0,33), bett (4) och träffyta (0,7): de skilde sig
# bara i modellens storlek och päls. Sajten lovade "they are not reskins", och
# det var sant om MODELLERNA — men en bernhardshund sprang lika fort och bet
# lika hårt som en jack russell. Grispaketet gjorde tvärtom två dagar senare,
# och den regeln gäller här också: man väljer hund efter uppgift, inte färg.
#
# Varje rad kopplar till en mekanik som redan finns. Taxen är avlad för att
# gräva, retrievern för att apportera, den lilla hunden hör och skäller först.
#
#   liv    minecraft:health
#   fart   minecraft:movement
#   bett   attackskadan i vaktläge
#   apport hur långt hunden letar efter något att hämta (pickup_items max_dist)
#   grav   multiplikator på grävpausen — LÄGRE betyder oftare
#   varsel hur långt hunden känner ett hot i vaktläge
RASER = [
    ("truffle", "Truffle", "Pomeranian", "ludd", 0.68, "plains",
     dict(pals=(74, 54, 42), skugga=(44, 32, 26), under=(156, 114, 74),
          ogon=(206, 150, 70), monster=["brost"]), {'liv': 12, 'fart': 0.34, 'bett': 2, 'apport': 10, 'grav': 1.1, 'varsel': 20}),
    ("rufus", "Rufus", "Golden Retriever", "hang", 1.05, "forest",
     dict(pals=(214, 166, 92), skugga=(172, 126, 62), under=(240, 216, 170),
          ogon=(92, 62, 36), monster=["brost"]), {'liv': 22, 'fart': 0.33, 'bett': 4, 'apport': 24, 'grav': 1.0, 'varsel': 14}),
    ("kelda", "Kelda", "Siberian Husky", "normal", 1.0, "taiga",
     dict(pals=(176, 182, 192), skugga=(72, 78, 90), under=(242, 244, 248),
          ogon=(96, 178, 210), monster=["mask", "brost", "sockor"]), {'liv': 22, 'fart': 0.34, 'bett': 4, 'apport': 16, 'grav': 1.0, 'varsel': 14}),
    ("pepper", "Pepper", "Border Collie", "hang", 0.95, "plains",
     dict(pals=(44, 42, 46), skugga=(26, 24, 28), under=(238, 238, 234),
          ogon=(118, 84, 48), monster=["brost", "blas", "sockor"]), {'liv': 20, 'fart': 0.35, 'bett': 4, 'apport': 18, 'grav': 1.0, 'varsel': 16}),
    ("pickle", "Pickle", "Dachshund", "kort", 0.8, "plains",
     dict(pals=(138, 74, 40), skugga=(88, 44, 24), under=(196, 132, 78),
          ogon=(70, 48, 30), monster=["brost"]), {'liv': 16, 'fart': 0.27, 'bett': 3, 'apport': 12, 'grav': 0.5, 'varsel': 12}),
    ("bruno", "Bruno", "Saint Bernard", "tung", 1.2, "extreme_hills",
     dict(pals=(186, 116, 62), skugga=(120, 68, 34), under=(246, 244, 238),
          ogon=(86, 58, 34), monster=["brost", "blas", "sockor"]), {'liv': 26, 'fart': 0.28, 'bett': 6, 'apport': 14, 'grav': 1.2, 'varsel': 12}),
    ("dot", "Dot", "Dalmatian", "hang", 1.0, "plains",
     dict(pals=(240, 240, 236), skugga=(38, 36, 38), under=(250, 250, 248),
          ogon=(96, 74, 52), monster=["flackar"]), {'liv': 20, 'fart': 0.36, 'bett': 4, 'apport': 16, 'grav': 1.0, 'varsel': 14}),
    ("scout", "Scout", "Jack Russell Terrier", "liten", 0.75, "plains",
     dict(pals=(238, 234, 224), skugga=(176, 120, 62), under=(250, 248, 244),
          ogon=(74, 54, 38), monster=["sadel", "brost"]), {'liv': 14, 'fart': 0.4, 'bett': 3, 'apport': 14, 'grav': 0.8, 'varsel': 14}),
]


# SPRÅKEN. sv_SE.lang innehöll ENGELSK text, ordagrant kopierad från en_US —
# paketet lovade svenska i languages.json och levererade inte. Antingen tar man
# bort språket eller så översätter man det; familjen spelar på svenska, så det
# blev det senare.
RAS_SV = {"Pomeranian": "Pomeranian", "Golden Retriever": "Golden retriever",
          "Siberian Husky": "Siberian husky", "Border Collie": "Border collie",
          "Dachshund": "Tax", "Saint Bernard": "Sankt bernhardshund",
          "Dalmatian": "Dalmatiner", "Jack Russell Terrier": "Jack russell-terrier"}
SPRAK = {
    "en_US": dict(agg="Spawn {n}", boll="Fetch Ball", vissla="Dog Whistle",
                  kommando="Command", halsband="Put on collar",
                  apport="Your dog brings it back.",
                  lage=("Follow", "Stay", "Guard"),
                  vissla_kom="Your dogs come running.",
                  vissla_ingen="No dogs answered.",
                  grav="Your dog dug something up.",
                  vakt="Your dog growls at something nearby."),
    "sv_SE": dict(agg="Skapa {n}", boll="Apportboll", vissla="Hundvissla",
                  kommando="Kommando", halsband="Sätt på halsband",
                  apport="Hunden kommer tillbaka med den.",
                  lage=("Följ", "Stanna", "Vakta"),
                  vissla_kom="Dina hundar kommer springande.",
                  vissla_ingen="Ingen hund svarade.",
                  grav="Hunden grävde upp något.",
                  vakt="Hunden morrar åt något i närheten."),
}


def sprakrader(spr):
    t = SPRAK[spr]
    rader = []
    for rasid, namn, ras, _k, _s, _b, _f, _m in RASER:
        r = RAS_SV[ras] if spr == "sv_SE" else ras
        rader += [f"entity.{NS}:{rasid}.name={namn} ({r})",
                  f"entity.{rasid}.name={namn} ({r})",
                  f"item.spawn_egg.entity.{NS}:{rasid}.name=" + t["agg"].format(n=namn)]
    rader += [f"item.{NS}:boll.name=" + t["boll"], f"item.{NS}:vissla.name=" + t["vissla"],
              "action.interact.command=" + t["kommando"],
              "action.interact.collar=" + t["halsband"],
              # SKRIPTETS KVITTON hör hemma i tabellen, inte i skriptet. Lades de
              # till i .lang-filen för hand försvann de nästa gång generatorn
              # kördes, för den skriver om filen från grunden.
              f"{NS}.apport.klar=" + t["apport"],
              f"{NS}.vissla.kom=" + t["vissla_kom"],
              f"{NS}.vissla.ingen=" + t["vissla_ingen"],
              f"{NS}.grav=" + t["grav"], f"{NS}.vakt=" + t["vakt"]]
    rader += [f"{NS}.lage.{i}=" + n for i, n in enumerate(t["lage"])]
    return rader


def ikon(rasid, farg, oron):
    """16x16 hundansikte — samma formspråk som kattpaketets spawnägg."""
    N = 16
    px = [[(0, 0, 0, 0)] * N for _ in range(N)]

    def rect(x0, y0, w, h, c):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if 0 <= x < N and 0 <= y < N:
                    px[y][x] = c
    p, s, u, o = farg["pals"], farg["skugga"], farg["under"], farg["ogon"]
    rect(3, 3, 10, 11, p + (255,))
    if oron == "upp":
        rect(3, 0, 3, 4, s + (255,))
        rect(10, 0, 3, 4, s + (255,))
    else:                                   # hängöron utanför skallen
        rect(1, 3, 2, 8, s + (255,))
        rect(13, 3, 2, 8, s + (255,))
    rect(3, 3, 10, 1, sh(p, 1.16))
    rect(5, 7, 6, 5, u + (255,))            # nosparti
    rect(6, 10, 4, 2, (24, 22, 22, 255))
    rect(5, 6, 2, 2, o + (255,))
    rect(9, 6, 2, 2, o + (255,))
    rect(3, 13, 10, 1, sh(p, 0.7))
    rr.write_png(f"{RP}/textures/items/dc_{rasid}.png", N, N, px)


def entitet(rasid, skala, matt):
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
                            # 0 inget, 1 boll, 2 pinne, 3 ben — vilken av
                            # munkuberna renderaren ska visa
                            f"{NS}:bar": {"type": "int", "range": [0, 3],
                                          "default": 0, "client_sync": True},
                            # 0 inget halsband, annars färgens nummer i HALSBAND
                            f"{NS}:halsband": {"type": "int", "range": [0, len(HALSBAND)],
                                               "default": 0, "client_sync": True}}},
        "components": {
            "minecraft:type_family": {"family": ["dc_hund", "mob"]},
            "minecraft:health": {"value": matt["liv"], "max": matt["liv"]},
            # TRÄFFYTAN FÖLJER STORLEKEN. Den var 0,7 för alla åtta, så en
            # pomeranian på skala 0,68 var lika bred att gå in i som en
            # bernhardshund på 1,2. minecraft:scale skalar modellen, inte
            # kollisionslådan.
            "minecraft:collision_box": {"width": round(0.7 * skala, 2),
                                        "height": round(0.9 * skala, 2)},
            "minecraft:physics": {}, "minecraft:pushable": {"is_pushable": True},
            "minecraft:movement": {"value": matt["fart"]},
            "minecraft:movement.basic": {}, "minecraft:jump.static": {},
            "minecraft:navigation.walk": {"can_path_over_water": True, "avoid_water": True},
            "minecraft:nameable": {},
            "minecraft:behavior.float": {"priority": 0},
            "minecraft:behavior.panic": {"priority": 1, "speed_multiplier": 1.4},
            # PRIORITETERNA MÅSTE VARA UNIKA i varje kombination av grupper som
            # kan vara aktiva samtidigt. Två mål med samma siffra är
            # odefinierat i Bedrock — det ena kan tyst falla bort. look_at_player
            # låg på 8, samma som vaktlägets follow_owner.
            "minecraft:behavior.look_at_player": {"priority": 10, "look_distance": 8},
            "minecraft:behavior.random_look_around": {"priority": 11},
            # SKÄLLET. event_name pekar in i sounds.json; går namnet fel blir
            # det tyst utan felmeddelande.
            # SÄLLAN. Sju sekunder med tolv i spridning betyder ett skall var
            # trettonde sekund PER HUND — tre hundar i följe blir en hund som
            # skäller var fjärde sekund, och då stänger man av ljudet.
            "minecraft:ambient_sound_interval": {"value": 20.0, "range": 30.0,
                                                 "event_name": "ambient"},
            # INGEN minecraft:equippable. Den satt här först, i tron att
            # pickup_items behövde någonstans att lägga bytet. Den registreras
            # inte ens: skriptet ser ingen equippable-komponent på hunden, och
            # vanilla FÖRSTÖR föremålet när moben når fram (även med
            # minecraft:inventory monterad — den platsen förblev tom). Därför
            # äger skriptet bärandet; vaniljas enda uppgift är att gå dit.
            #
            # SHAREABLES ÄR NYCKELN TILL APPORTEN, och den kostade åtta
            # serverkörningar att hitta. minecraft:behavior.pickup_items ensam
            # gör INGENTING: hunden fick beteendet, gruppen lades till, och den
            # gick ändå aldrig fram till bollen — i alla varianter vi provade.
            # Räven i samma värld tog samma boll varje gång. Skillnaden var den
            # här komponenten: den är mobens ÖNSKELISTA, och utan den finns det
            # inget föremål värt att gå till.
            "minecraft:shareables": {"all_items": False, "items": [
                {"item": i, "want_amount": 1, "surplus_amount": 1, "priority": 0}
                for i in APPORTBARA]},
            # TÄMJNING MED BEN, inte fisk. 0.33 per försök: några ben, inte ett
            # — att tämja ska kosta något, som hos katterna.
            "minecraft:tameable": {"probability": 0.33, "tame_items": ["bone"],
                                   "tame_event": {"event": f"{NS}:on_tame", "target": "self"}},
        },
        "component_groups": {
            f"{NS}:tamed": {
                "minecraft:is_tamed": {},
                # PERSISTENT BARA NÄR HUNDEN ÄR NÅGONS. Den satt i
                # baskomponenterna, vilket betyder att varenda vildhund som
                # någonsin spawnat blir kvar för alltid — åtta raser som aldrig
                # despawnar sväller en värld år efter år. Vaniljas djur är inte
                # persistenta; en tämjd hund ska däremot aldrig försvinna.
                "minecraft:persistent": {},
                "minecraft:sittable": {},
                "minecraft:behavior.stay_while_sitting": {"priority": 3},
                # MATEN LÄKER. Kött av alla slag, som hos vargen.
                "minecraft:healable": {"force_use": True, "items": [
                    {"item": i, "heal_amount": h} for i, h in
                    (("beef", 3), ("cooked_beef", 5), ("chicken", 2), ("cooked_chicken", 4),
                     ("porkchop", 3), ("cooked_porkchop", 5), ("mutton", 2), ("cooked_mutton", 4),
                     ("rabbit", 2), ("cooked_rabbit", 4), ("rotten_flesh", 2))]},
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
                    "interact_text": "action.interact.command"},
                    # HALSBANDET SÄTTS MED FÄRGÄMNE. Samma väg som kommandot:
                    # en interaktion per färg, filtrerad på vad ägaren håller i.
                    *[{"on_interact": {"filters": {"all_of": [
                        {"test": "is_family", "subject": "other", "value": "player"},
                        {"test": "is_owner", "subject": "other"},
                        {"test": "has_equipment", "domain": "hand", "subject": "other",
                         "value": f"{f}_dye"}]},
                        "event": f"{NS}:halsband_{i}", "target": "self"},
                        "use_item": True, "play_sounds": "armor.equip_leather",
                        "interact_text": "action.interact.collar"}
                      for i, (f, _c) in enumerate(HALSBAND, 1)]]},
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
                "minecraft:behavior.follow_owner": {"priority": 9, "speed_multiplier": 1.0,
                                                    "start_distance": 14, "stop_distance": 6},
                "minecraft:behavior.owner_hurt_by_target": {"priority": 4},
                "minecraft:behavior.owner_hurt_target": {"priority": 5},
                "minecraft:behavior.nearest_attackable_target": {
                    "priority": 6, "must_see": True, "reselect_targets": True,
                    "within_radius": 12,
                    "entity_types": [{"filters": {"any_of": [
                        {"test": "is_family", "subject": "other", "value": "monster"}]},
                        "max_dist": 12}]},
                "minecraft:behavior.melee_attack": {"priority": 7},
                "minecraft:attack": {"damage": matt["bett"]},
            },
            # APPORT: vaniljas egen upplockning gör navigeringen åt oss. Att
            # skriptstyra en entitet fram till ett föremål går inte — det finns
            # ingen väg att sätta ett mål från skript.
            f"{NS}:apporterar": {
                # INGEN follow_owner HÄR. Den finns redan i hund:foljer med
                # prioritet 6; två follow_owner samtidigt är två mål som slåss
                # om samma hund. Upplockningen har lägre siffra och vinner
                # därför över hemgåendet så länge bollen ligger kvar.
                "minecraft:behavior.pickup_items": {
                    "priority": 2, "max_dist": matt["apport"], "goal_radius": 1.6,
                    "speed_multiplier": 1.3, "pickup_based_on_chance": False,
                    "track_target": True},
            },
            f"{NS}:vuxen": {"minecraft:scale": {"value": skala}},
            f"{NS}:valp": {"minecraft:scale": {"value": round(skala / 2, 3)},
                           "minecraft:is_baby": {},
                           "minecraft:ageable": {"duration": 1200, "grow_up": {
                               "event": f"{NS}:grow_up", "target": "self"},
                               "feed_items": ["bone", "beef", "chicken", "porkchop"]}},
            # PARNING: två mätta, tämjda hundar av samma ras ger en valp.
            f"{NS}:parar": {
                "minecraft:breedable": {
                    "require_tame": True, "require_full_health": True,
                    "breeds_with": [{"mate_type": f"{NS}:{rasid}",
                                     "baby_type": f"{NS}:{rasid}",
                                     "breed_event": {"event": f"{NS}:fodd", "target": "baby"}}],
                    "love_filters": {"test": "has_component", "subject": "self",
                                     "operator": "!=", "value": "minecraft:is_baby"},
                    "breed_items": ["beef", "cooked_beef", "porkchop", "cooked_porkchop"]},
                "minecraft:behavior.breed": {"priority": 4, "speed_multiplier": 1.0},
            },
        },
        "events": {
            f"{NS}:on_tame": {"add": {"component_groups": [f"{NS}:tamed", f"{NS}:foljer",
                                                           f"{NS}:parar"]},
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
            **{f"{NS}:halsband_{i}": {"set_property": {f"{NS}:halsband": i}}
               for i in range(1, len(HALSBAND) + 1)},
            f"{NS}:halsband_av": {"set_property": {f"{NS}:halsband": 0}},
            # VISSLAN sätter hunden i följaläge oavsett var den stod. Utan den
            # här händelsen kommer en hund i stannaläge springande och blir
            # sedan stående — då är visslan en teleport, inte ett kommando.
            f"{NS}:till_foljer": {"set_property": {f"{NS}:lage": 0},
                                  "add": {"component_groups": [f"{NS}:foljer"]},
                                  "remove": {"component_groups": [f"{NS}:stannar",
                                                                  f"{NS}:vaktar"]}},
            f"{NS}:apport_pa": {"add": {"component_groups": [f"{NS}:apporterar"]}},
            f"{NS}:apport_av": {"remove": {"component_groups": [f"{NS}:apporterar"]}},
            "minecraft:entity_spawned": {"add": {"component_groups": [f"{NS}:vuxen"]}},
            # VALPEN ÄRVER TAMHETEN. En valp född till tämjda föräldrar som
            # sedan måste tämjas om vore bara irriterande.
            # VALPEN MÅSTE TAPPA hund:vuxen. minecraft:entity_spawned hinner
            # lägga på den innan parningens hund:fodd kör, och då bär ungen TVÅ
            # minecraft:scale — vilken som vinner är odefinierat, och valpen kan
            # födas fullvuxen.
            f"{NS}:fodd": {"add": {"component_groups": [f"{NS}:valp", f"{NS}:tamed",
                                                        f"{NS}:foljer"]},
                           "remove": {"component_groups": [f"{NS}:vuxen"]},
                           "set_property": {f"{NS}:tam": 1}},
            f"{NS}:grow_up": {"add": {"component_groups": [f"{NS}:vuxen", f"{NS}:parar"]},
                              "remove": {"component_groups": [f"{NS}:valp"]}},
        }}}
    json.dump(e, open(f"{BP}/entities/{rasid}.json", "w"), indent=2)


def klient(rasid, kropp):
    d = {"format_version": "1.10.0", "minecraft:client_entity": {"description": {
        "identifier": f"{NS}:{rasid}",
        "materials": {"default": "entity_alphatest"},
        "textures": {"default": f"textures/entity/{rasid}"},
        "geometry": {"default": f"geometry.hund_{kropp}"},
        # Bennamnen är head/body/leg0-3/tail — samma som vaniljas
        # fyrfotingsanimationer förväntar sig.
        "animations": {"walk": "animation.quadruped.walk",
                       "look_at_target": "animation.common.look_at_target"},
        "scripts": {"animate": [{"walk": "query.modified_move_speed"}, "look_at_target"]},
        "render_controllers": ["controller.render.hund"],
        "spawn_egg": {"texture": f"dc_{rasid}", "texture_index": 0}}}}
    json.dump(d, open(f"{RP}/entity/{rasid}.json", "w"), indent=2)


def spawnregel(rasid, biom, vikt):
    json.dump({"format_version": "1.8.0", "minecraft:spawn_rules": {
        "description": {"identifier": f"{NS}:{rasid}", "population_control": "animal"},
        "conditions": [{"minecraft:spawns_on_surface": {},
                        "minecraft:brightness_filter": {"min": 7, "max": 15,
                                                        "adjust_for_weather": False},
                        "minecraft:difficulty_filter": {"min": "easy", "max": "hard"},
                        "minecraft:weight": {"default": vikt},
                        "minecraft:herd": {"min_size": 1, "max_size": 2},
                        "minecraft:biome_filter": {"test": "has_biome_tag",
                                                   "operator": "==", "value": biom}}]}},
        open(f"{BP}/spawn_rules/{rasid}.json", "w"), indent=2)


def visslan():
    """Hundvisslan: ett tryck och alla dina hundar kommer.

    Att leta reda på en hund som blivit kvar tre dalar bort är inte roligt, och
    ett stannakommando man glömt är den vanligaste vägen dit. Visslan är därför
    inte en genväg förbi mekaniken — den är räddningen ur den."""
    json.dump({"format_version": "1.20.50", "minecraft:item": {
        "description": {"identifier": f"{NS}:vissla",
                        "menu_category": {"category": "equipment"}},
        "components": {"minecraft:icon": {"texture": "dc_vissla"},
                       "minecraft:display_name": {"value": "Dog Whistle"},
                       "minecraft:max_stack_size": 1,
                       # AVSVALNING i föremålet, inte i skriptet: spelaren ser
                       # den snurra i handen och förstår varför inget händer.
                       "minecraft:cooldown": {"category": "hund_vissla", "duration": 6.0}}}},
        open(f"{BP}/items/vissla.json", "w"), indent=2)
    json.dump({"format_version": "1.20.10", "minecraft:recipe_shapeless": {
        "description": {"identifier": f"{NS}:vissla"},
        "tags": ["crafting_table"],
        "ingredients": [{"item": "minecraft:iron_ingot"}, {"item": "minecraft:bone"}],
        "unlock": [{"item": "minecraft:bone"}],
        "result": {"item": f"{NS}:vissla"}}},
        open(f"{BP}/recipes/vissla.json", "w"), indent=2)
    N = 16
    px = [[(0, 0, 0, 0)] * N for _ in range(N)]

    def rect(x0, y0, w, h, c):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if 0 <= x < N and 0 <= y < N:
                    px[y][x] = c
    METALL, LJUS, MORK = (186, 190, 198, 255), (232, 236, 242, 255), (108, 112, 122, 255)
    rect(3, 6, 10, 5, METALL)          # visselpipans kropp
    rect(3, 6, 10, 1, LJUS)
    rect(3, 10, 10, 1, MORK)
    rect(1, 7, 3, 3, METALL)           # munstycket
    rect(1, 7, 3, 1, LJUS)
    rect(8, 8, 3, 1, MORK)             # ljudspringan
    rect(12, 3, 2, 4, MORK)            # ögla att hänga i
    rect(11, 2, 4, 1, MORK)
    rr.write_png(f"{RP}/textures/items/dc_vissla.png", N, N, px)


def ljud():
    """Rösterna. Vi har inga egna ljudfiler och kan inte göra några här, så
    hundarna lånar vargens ljudhändelser — de finns i varje installation.

    TONHÖJDEN SKILJER RASERNA ÅT. En bernhardshund och en pomeranian som låter
    exakt likadant är två skinn på samma hund; skalan styr pitchen, så den
    lilla gnyr ljust och den tunga morrar mörkt.

    Går ett händelsenamn fel blir det TYST, utan ett ord i någon logg — det
    finns ingen facitlista att kontrollera mot på servern (BDS resurspaket
    innehåller inga ljud). Därför bara vargens välkända namn."""
    ent = {}
    for rasid, _namn, _ras, _kropp, skala, _biom, _farg, _matt in RASER:
        pitch = round(1.6 - 0.6 * skala, 2)
        ent[f"{NS}:{rasid}"] = {
            "volume": 0.9, "pitch": [round(pitch - 0.08, 2), round(pitch + 0.08, 2)],
            "events": {"ambient": "mob.wolf.bark", "hurt": "mob.wolf.hurt",
                       "death": "mob.wolf.death", "step": "mob.wolf.step",
                       "ambient.tame": "mob.wolf.panting"}}
    json.dump({"format_version": "1.14.0",
               "entity_sounds": {"entities": ent}},
              open(f"{RP}/sounds.json", "w"), indent=2)


def bollen():
    """Apportbollen: föremålet man kastar, plus dess recept och ikon.

    Ull och slem — mjukt och studsigt, och båda finns tidigt i ett spel. Att
    den är ett EGET föremål (och inte bara en pinne) gör att skriptet kan
    skilja "kastad boll" från allt annat som ligger på marken."""
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
    for m in ("models/entity", "render_controllers", "textures/entity", "textures/items", "entity"):
        os.makedirs(f"{RP}/{m}", exist_ok=True)
    # SPAWNVIKTEN DELAS INOM BIOMET. Fem raser i plains med vikt 3 var blev
    # samlad vikt 15 — nästan dubbelt mot vaniljas varg (8), alltså hundar
    # överallt. Vikten räknas nu fram ur hur många raser som delar biomet.
    # RASTABELLEN TILL SKRIPTET. Grävfrekvensen och varslet bor i main.js, och
    # skriptet kan inte läsa entitets-JSON — en handskriven kopia hade glidit
    # isär från RASER vid första justeringen. Samma lösning som grispaketets.
    tab = {f"{NS}:{r[0]}": {"grav": r[7]["grav"], "varsel": r[7]["varsel"]} for r in RASER}
    open(f"{BP}/scripts/raser.js", "w", encoding="utf-8").write(
        "// GENERERAD AV tools/make_dogs.py — ändra i RASER, inte här.\n"
        "export const RASER = " + json.dumps(tab, indent=1) + ";\n")

    antal = Counter(r[5] for r in RASER)
    VIKT = {b: max(1, round(4 / n)) for b, n in antal.items()}
    delar, uv = skriv_geometrier()
    renderarkontroller()
    ljud()
    itex = {"resource_pack_name": "loyal", "texture_name": "atlas.items", "texture_data": {}}
    for rasid, namn, ras, kropp, skala, biom, farg, matt in RASER:
        pals(rasid, delar[kropp], uv[kropp], farg)
        ikon(rasid, farg, KROPPAR[kropp][5])
        entitet(rasid, skala, matt)
        klient(rasid, kropp)
        spawnregel(rasid, biom, VIKT[biom])
        itex["texture_data"][f"dc_{rasid}"] = {"textures": f"textures/items/dc_{rasid}"}
        print(f"  {namn:8} {ras:22} {kropp:7} skala {skala:<5} biom {biom}")
    bollen()
    visslan()
    itex["texture_data"]["dc_boll"] = {"textures": "textures/items/dc_boll"}
    itex["texture_data"]["dc_vissla"] = {"textures": "textures/items/dc_vissla"}
    json.dump(itex, open(f"{RP}/textures/item_texture.json", "w"), indent=2)
    for pack in (BP, RP):
        for spr in SPRAK:
            open(f"{pack}/texts/{spr}.lang", "w", encoding="utf-8").write(
                "\n".join(sprakrader(spr)) + "\n")
        json.dump(list(SPRAK), open(f"{pack}/texts/languages.json", "w"))
    print(f"  {len(RASER)} raser, {len(KROPPAR)} kroppar, "
          f"{len(sprakrader('en_US'))} språkrader x {len(SPRAK)} språk")
