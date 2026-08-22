#!/usr/bin/env python3
"""Projektloggan — den inramade rutan, samma recept som kattpaketets.

  publish/logo.png   512x512, används som projektavatar och på sajten

VARFÖR DEN SER UT SÅ HÄR står i kattpaketets logga och gäller ordagrant här:

  * TRE STORA DJUR, inte sex små. Sex katter i två rader blev en klump som
    inte gick att tyda i CurseForge-listan; grannarna som fungerar har EN
    eller TRE stora figurer.
  * MÖRK BOTTEN. Listans grannar är dagsljusbilder; en natthimmel skiljer ut
    rutan, och ljusa pälsar lyfter mot mörkt.
  * VIT KONTUR runt varje hund. Utan den smälter en mörk hund ihop med natten.
  * RAM I FYRA LAGER MED HÖRNKLOSSAR. Det är hörnklossarna som får ramen att
    läsa som en ram och inte som en kant.
  * INGEN TEXT. Butiken skriver ut projektnamnet bredvid avataren ändå, och
    utan textremsa får hundarna hela ytan.

Urvalet är gjort på KONTRAST och SILUETT, inte på vilken ras som är
populärast: Bruno är stor och tung, Dot är vit med svarta fläckar, Scout är
liten. Storlek, färg och form skiljer sig samtidigt — då ser man på en halv
sekund att paketet innehåller olika hundar.

    python3 tools/make_logo.py
"""
import os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/opt/purrfect-companions")
sys.path.insert(0, f"{BASE}/tools")
import render_regression as rr
import render_dogs as rd

P = 512
FRAM = int(P * 0.54)                       # horisonten
TOM = (0, 0, 0, 0)
NYCKEL = (255, 0, 255, 255)

# (ras, x-andel, fotlinje, höjd i px, boll i munnen, halsbandsfärg)
# HÖJDERNA ÄR RÄKNADE MOT RAMEN: fotlinjen ligger på 0,86 och ramen på 0,97,
# så tassarna hamnar innanför. En logga med avklippta fötter ser trasig ut.
# HÖJDERNA SÄNKTA efter första försöket: spriten beskärs till sitt innehåll,
# så samma siffra ger en STÖRRE hund än i kattloggan, där renderarens tomma
# luft räknades in. Tre hundar på 272-286 px fyllde hela rutan, gick in i
# varandra och fick tassarna avklippta av ramen.
UPPSTALLNING = [
    ("bruno", 0.200, 0.855, 218, 0, 1),
    ("dot", 0.500, 0.890, 232, 1, 5),
    ("scout", 0.800, 0.855, 200, 0, 4),
]


def brus(n):
    n = (n * 1103515245 + 12345) & 0x7FFFFFFF
    return (n >> 16) & 0x7FFF


duk = [[(0, 0, 0, 255)] * P for _ in range(P)]
for y in range(P):
    k = min(1.0, y / FRAM)
    for x in range(P):
        # svag gloria mitt i bilden: kanterna mörka, men ljusare där hundarna
        # står — annars sjunker de in i botten
        d = (((x - P * 0.5) ** 2 + (y - P * 0.62) ** 2) ** 0.5) / (P * 0.62)
        g = max(0.0, 1.0 - d) ** 2 * 34
        duk[y][x] = (int(16 + 26 * k + g), int(20 + 34 * k + g), int(44 + 46 * k + g * 1.1), 255)


def rita(x0, y0, w, h, c):
    for y in range(int(y0), int(y0 + h)):
        for x in range(int(x0), int(x0 + w)):
            if 0 <= y < P and 0 <= x < P:
                duk[y][x] = c


B = 16                                     # blockstorlek, samma pixelspråk som hjältebilden
for i in range(46):                        # stjärnor, glesa och deterministiska
    n = brus(i * 977)
    ljus = 170 + (n % 70)
    rita(n % P, (n // 7) % int(P * 0.42), 3, 3, (ljus, ljus, min(255, ljus + 20), 255))
for bx in range(0, P // B + 1):            # kullar
    rita(bx * B, FRAM - B - (brus(bx * 7) % 2) * (B // 2), B, 3 * B, (22, 40, 30, 255))
GRAS = [(30, 54, 40), (25, 46, 34), (36, 62, 44), (22, 42, 31)]
for by, y in enumerate(range(FRAM, P, B)):
    for bx, x in enumerate(range(0, P, B)):
        n = brus(bx * 31 + by * 17)
        f = 0.9 + min(0.22, by * 0.03)
        rita(x, y, B, B, tuple(min(255, int(v * f)) for v in GRAS[n % 4]) + (255,))
        if n % 5 == 0:
            rita(x + (n % 11), y + 2, 2, B // 3, (44, 74, 50, 255))
        if n % 41 == 0:                    # nattblommor, dova
            rita(x + 5, y + 5, 4, 4, [(196, 168, 96, 255), (206, 206, 214, 255),
                                      (190, 112, 148, 255)][n % 3])


def blit(dst, src, cx, cy, out_h):
    """Skala och klistra, med TOM som genomskinlig. Jämför mot ett VÄRDE, inte
    mot alfa — kattloggan satte bara alfa=0 och behöll färgen, och då matchade
    ingenting och varje djur fick en svart ruta runt sig."""
    sh, sw = len(src), len(src[0])
    k = sh / out_h
    out_w = int(sw / k)
    for oy in range(out_h):
        for ox in range(out_w):
            p = src[min(sh - 1, int(oy * k))][min(sw - 1, int(ox * k))]
            if p == TOM:
                continue
            px, py = cx - out_w // 2 + ox, cy - out_h // 2 + oy
            if 0 <= px < P and 0 <= py < P:
                dst[py][px] = p


for rasid, fx, fy, hojd, bar, hals in UPPSTALLNING:
    geoid, tex = next((g, t) for r, g, t in rd.rasklient() if r == rasid)
    src = rd.rita(geoid, tex, 300, 300, yaw=26, pitch=10, bar=bar, halsband=hals,
                  bakgrund=NYCKEL)
    nyckl = [[TOM if p[:3] == NYCKEL[:3] else (p[0], p[1], p[2], 255) for p in rad]
             for rad in src]
    # SPRITEN BESKÄRS till sitt innehåll, annars styr renderarens tomma luft
    # var hunden hamnar och fotlinjen blir olika för olika kroppar.
    rader = [y for y in range(300) if any(p != TOM for p in nyckl[y])]
    kol = [x for x in range(300) if any(nyckl[y][x] != TOM for y in rader)]
    nyckl = [rad[kol[0]:kol[-1] + 1] for rad in nyckl[rader[0]:rader[-1] + 1]]
    sx, sy = int(P * fx), int(P * fy)
    # ELLIPS UNDER HUNDEN: en mjuk skugga grundar djuret och skiljer det från
    # gräset bättre än en rak stapel.
    for y in range(sy - hojd // 12, sy + hojd // 12):
        for x in range(sx - hojd // 3, sx + hojd // 3):
            e = ((x - sx) / (hojd / 3.0)) ** 2 + ((y - sy) / (hojd / 12.0)) ** 2
            if e < 1.0 and 0 <= y < P and 0 <= x < P:
                f = (1.0 - e) * 0.55
                p = duk[y][x]
                duk[y][x] = (int(p[0] * (1 - f)), int(p[1] * (1 - f)), int(p[2] * (1 - f)), 255)
    ljus = [[(236, 244, 252, 255) if p != TOM else TOM for p in rad] for rad in nyckl]
    for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (3, -3), (-3, 3), (3, 3)):
        blit(duk, ljus, sx + dx, sy - hojd // 2 + dy, hojd)
    blit(duk, nyckl, sx, sy - hojd // 2, hojd)

# TASSAVTRYCK i himlen — hundarnas motsvarighet till kattloggans hjärtan. De
# får INTE ligga över hundarna: prydnad framför motivet gör tvärtom mot vad en
# logga ska göra.
def tass(hx, hy, sk, c):
    # TÅRNA MÅSTE HA LUFT EMELLAN. Först låg de på 2*sk mellanrum och var
    # 2*sk breda — de gick ihop till en stapel och avtrycket såg ut som en
    # klump.
    for i, dy in enumerate((1, 0, 0, 1)):
        rita(hx + i * 3 * sk, hy + dy * sk, sk * 2, sk * 2, c)
    for j, (bredd, off) in enumerate(((7, 1), (9, 0), (9, 0), (7, 1))):
        rita(hx + off * sk, hy + (4 + j) * sk, bredd * sk, sk, c)


for hx, hy, sk in ((int(P * 0.07), int(P * 0.28), 3), (int(P * 0.87), int(P * 0.20), 4),
                   (int(P * 0.70), int(P * 0.34), 2)):
    tass(hx, hy, sk, (226, 190, 132, 255))

# RAMEN: fyra lager plus hörnklossar.
MORK, GULD, GLIMT = (18, 16, 22, 255), (214, 172, 78, 255), (255, 226, 150, 255)


def kant(t, c):
    for x in range(t, P - t):
        duk[t][x] = duk[P - 1 - t][x] = c
    for y in range(t, P - t):
        duk[y][t] = duk[y][P - 1 - t] = c


for t in range(0, 7):
    kant(t, MORK)
for t in range(7, 13):
    kant(t, GULD)
for t in range(13, 15):
    kant(t, MORK)
kant(15, GLIMT)
for hx in (0, P - 26):
    for hy in (0, P - 26):
        for y in range(hy, hy + 26):
            for x in range(hx, hx + 26):
                k = min(x - hx, y - hy, hx + 25 - x, hy + 25 - y)
                duk[y][x] = MORK if k < 4 else (GLIMT if k < 6 else GULD)

os.makedirs(f"{BASE}/publish", exist_ok=True)
rr.write_png(f"{BASE}/publish/logo.png", P, P, duk)
print(f"  publish/logo.png ({P}x{P})")
