#!/usr/bin/env python3
"""Renderar hundarna ur paketets EGNA filer, så man kan se dem utan Minecraft.

Servern renderar ingenting och det finns ingen klient på maskinen. Utan den här
bilden är enda sättet att veta hur en hund ser ut att fråga någon som har
spelet uppe — och då upptäcks fel som sneda ögon eller ben som smälter ihop
först efter en release. Katterna kostade flera varv på precis det.

Motorn är kattprojektets: samma kub-för-kub-rasterisering med z-buffert och
rotation kring benens pivotar.

    python3 tools/render_dogs.py            # publish/dogs.png, alla raser
    python3 tools/render_dogs.py truffle    # en enda, större
"""
import json, math, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/opt/purrfect-companions")
sys.path.insert(0, "/opt/purrfect-companions/tools/promo")
import render_regression as rr

RP = f"{BASE}/LoyalCompanions_RP"
GEO = {g["description"]["identifier"]: g
       for g in json.load(open(f"{RP}/models/entity/hund.geo.json"))["minecraft:geometry"]}

# En pose som sätter varje rörligt ben i arbete. Står något stilla här kan dess
# pivot vara hur fel som helst utan att synas.
POSE = {"head": (-8, 24, 0), "leg0": (26, 0, 0), "leg1": (-26, 0, 0),
        "leg2": (-22, 0, 0), "leg3": (22, 0, 0), "tail": (10, 0, 14)}


def rasklient():
    ut = []
    for f in sorted(os.listdir(f"{RP}/entity")):
        d = json.load(open(f"{RP}/entity/{f}"))["minecraft:client_entity"]["description"]
        ut.append((d["identifier"].split(":")[1], d["geometry"]["default"],
                   d["textures"]["default"]))
    return ut


def rita(geoid, texnamn, W, H, yaw=34, pitch=14, pose=POSE, bar=0, halsband=0,
         bakgrund=(22, 26, 34, 255)):
    tw, th, tex = rr.read_png(f"{RP}/{texnamn}.png")
    geo = GEO[geoid]
    ya, pa = math.radians(yaw), math.radians(pitch)
    # MUNKUBERNA visas bara när hunden bär något — annars ligger boll, pinne och
    # ben i högen samtidigt, precis det renderarkontrollern finns för att hindra.
    dolda = {n for i, n in enumerate(("mun_boll", "mun_pinne", "mun_ben"), 1) if i != bar}
    # HALSBANDEN ligger alla på samma plats, ett ben per färg; visas de
    # samtidigt blir det en enda grötig ring.
    dolda |= {f"hals{i}" for i in range(1, 9) if i != halsband}

    def cam(p):
        x, y, z = p
        xr = x * math.cos(ya) + z * math.sin(ya)
        zr = -x * math.sin(ya) + z * math.cos(ya)
        return (xr, y * math.cos(pa) - zr * math.sin(pa), zr * math.cos(pa) + y * math.sin(pa))

    ben = [(b["name"], b.get("pivot", [0, 0, 0]), b.get("cubes", []))
           for b in geo["bones"] if b["name"] not in dolda]
    hörn = [cam((x, y, z)) for x in (-9, 9) for y in (0, 21) for z in (-13, 11)]
    minx, maxx = min(c[0] for c in hörn), max(c[0] for c in hörn)
    miny, maxy = min(c[1] for c in hörn), max(c[1] for c in hörn)
    pad = int(min(W, H) * 0.05)
    sc = min((W - 2 * pad) / (maxx - minx), (H - 2 * pad) / (maxy - miny))
    offx = pad - minx * sc + (W - 2 * pad - (maxx - minx) * sc) / 2
    offy = pad - miny * sc + (H - 2 * pad - (maxy - miny) * sc) / 2
    cv = [[bakgrund] * W for _ in range(H)]
    zb = [[9e9] * W for _ in range(H)]
    for namn, pivot, kuber in ben:
        deg = pose.get(namn, (0, 0, 0))
        for c in kuber:
            ox, oy, oz = c["origin"]; w, h, d = c["size"]; U, V = c["uv"]
            F = rr.faces(U, V, w, h, d)
            fns = {"top": lambda a, b: (ox + a * w, oy + h, oz + b * d),
                   "bottom": lambda a, b: (ox + a * w, oy, oz + b * d),
                   "north": lambda a, b: (ox + a * w, oy + (1 - b) * h, oz),
                   "south": lambda a, b: (ox + a * w, oy + (1 - b) * h, oz + d),
                   "east": lambda a, b: (ox + w, oy + (1 - b) * h, oz + a * d),
                   "west": lambda a, b: (ox, oy + (1 - b) * h, oz + a * d)}
            for fnamn, fn in fns.items():
                u0, v0, fw, fh = F[fnamn]; skugga = rr.SH[fnamn]
                steg = max(int(max(fw, fh) * sc * 1.6), 10)
                for i in range(steg + 1):
                    for j in range(steg + 1):
                        a, b = i / steg, j / steg
                        p = fn(a, b)
                        X, Y, Z = cam(rr.rot(p, pivot, deg) if any(deg) else p)
                        px = int(X * sc + offx); py = int(H - (Y * sc + offy))
                        if not (0 <= px < W and 0 <= py < H) or Z >= zb[py][px]:
                            continue
                        col = tex[min(th - 1, max(0, int(v0 + b * fh)))][
                            min(tw - 1, max(0, int(u0 + a * fw)))]
                        if col[3] < 8:
                            continue
                        cv[py][px] = (int(col[0] * skugga), int(col[1] * skugga),
                                      int(col[2] * skugga), 255)
                        zb[py][px] = Z
    return cv


def ark():
    """Kontaktkarta över alla raser — en PRODUKTBILD, inte en felsökningsdump.

    Första versionen var åtta rutor med hård rutnätslinje mot marinblå botten.
    På sajten såg den ut som ett testutdrag: fel färg mot sidans gröna, och
    ingen kunde säga vilken hund som var vilken. Nu står namnen under
    hundarna och bottnen är samma toning som sidan."""
    import make_video as mv                       # text() lånas från trailern

    raser = rasklient()
    RUTA, ETIKETT, KOL = 200, 34, 4
    rader = math.ceil(len(raser) / KOL)
    W, H = RUTA * KOL, (RUTA + ETIKETT) * rader
    # mv.text() klipper mot SIN modulnivås W/H — trailerns 480x270. Utan den
    # här raden hamnar halva texten utanför duken.
    mv.W, mv.H = W, H
    # samma toning som sajtens body (#141a10 → #1c2416), så bilden sitter i
    # sidan i stället för att ligga ovanpå den
    duk = [[(int(20 + 8 * y / H), int(26 + 10 * y / H), int(16 + 6 * y / H), 255)
            for _ in range(W)] for y in range(H)]
    for i, (rasid, geoid, tex) in enumerate(raser):
        bild = rita(geoid, tex, RUTA, RUTA, bar=1 if i % 3 == 0 else 0,
                    halsband=(i % 8) + 1, bakgrund=(0, 0, 0, 0))
        rx, ry = (i % KOL) * RUTA, (i // KOL) * (RUTA + ETIKETT)
        # PANEL bakom varje hund: en aning ljusare än bottnen, med tunn kant.
        # Skiljer rutorna åt utan hårda rutnätslinjer, som fick första
        # versionen att se ut som ett kalkylark.
        for y in range(ry + 6, ry + RUTA - 2):
            for x in range(rx + 6, rx + RUTA - 6):
                kant = min(x - (rx + 6), y - (ry + 6), rx + RUTA - 7 - x, ry + RUTA - 3 - y)
                duk[y][x] = (40, 52, 34, 255) if kant < 1 else (27, 36, 23, 255)
        # VIT KONTUR, samma grepp som loggan. Utan den försvinner Pepper —
        # nästan svart päls mot mörk botten är ingen bild alls.
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, -1), (-1, 1), (1, 1)):
            for y in range(RUTA):
                for x in range(RUTA):
                    if not bild[y][x][3]:
                        continue
                    py, px = ry + y + dy, rx + x + dx
                    if ry <= py < ry + RUTA and rx <= px < rx + RUTA:
                        duk[py][px] = (232, 240, 246, 255)
        for y in range(RUTA):
            for x in range(RUTA):
                if bild[y][x][3]:
                    duk[ry + y][rx + x] = bild[y][x]
        mv.text(duk, rasid.upper(), rx + RUTA // 2, ry + RUTA + 8, 2, (217, 192, 122, 255))
    os.makedirs(f"{BASE}/publish", exist_ok=True)
    rr.write_png(f"{BASE}/publish/dogs.png", W, H, duk)
    print(f"  publish/dogs.png ({W}x{H}) — {', '.join(r[0] for r in raser)}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        rasid = sys.argv[1]
        geoid, tex = next((g, t) for r, g, t in rasklient() if r == rasid)
        rr.write_png(f"{BASE}/publish/dog-{rasid}.png", 400, 400,
                     rita(geoid, tex, 400, 400, bar=1, halsband=5))
        print(f"  publish/dog-{rasid}.png")
    else:
        ark()
