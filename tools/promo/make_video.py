#!/usr/bin/env python3
"""Trailer — renderad helt med vår egen z-buffrade motor.

Samma renderare som förhandsbilderna gör videorutor: gångcykeln animeras med
samma matematik som spelets animationer, kameran sveper, hundarna visas en i
taget. Ingen Minecraft-klient, ingen PIL, inget ljud (musik läggs på från
YouTubes licensfria bibliotek).

Rutor renderas i 480x270 och skalas till 1080p med NÄRMSTA GRANNE — pixellooken
är en del av Minecraft-estetiken, inte en kompromiss.

  publish/loyal-trailer.mp4   1080p
  publish/loyal-trailer.gif   480 px, loopar, till sajten

RÄKNEORDET FÖLJER LISTAN. Kattprojektets titelkort sa "FOUR" i klartext och
blev fel i samma stund som femte katten kom; en trailer som räknar fel är värre
än ingen trailer.

    python3 tools/promo/make_video.py            # full render
    python3 tools/promo/make_video.py --smoke    # var 25:e ruta, snabbkoll
"""
import math, multiprocessing, os, shutil, subprocess, sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, "/opt/purrfect-companions")
sys.path.insert(0, "/opt/purrfect-companions/tools/promo")
sys.path.insert(0, f"{BASE}/tools")
import render_regression as rr
import make_video as mv                     # FONT, text(), paste(), walk_pose()
import render_dogs as rd

W, H, FPS = 480, 270, 30
# mv.text() och mv.paste() klipper mot SIN modulnivås W/H. De råkar vara samma
# här, men raden står kvar för att nästa person som ändrar upplösningen inte
# ska tappa all text utanför duken.
mv.W, mv.H = W, H
UTKAT = "/tmp/loyal-frames"
MP4 = f"{BASE}/publish/loyal-trailer.mp4"
GIF = f"{BASE}/publish/loyal-trailer.gif"
SMOKE = "--smoke" in sys.argv
# BAKGRUNDEN ATT NYCKLA BORT är gräsets färg, inte magenta. mv.paste() skalar
# ner med boxmedelvärde och räknar med de genomskinliga pixlarnas FÄRG — med
# magenta bakom fick varje hund en rosa kant. Med gräsfärgen blir kanten
# osynlig. Samma rättelse som hjältebilden redan bär.
NYCKEL = (106, 152, 62, 255)
RAKNEORD = {1: "ONE", 2: "TWO", 3: "THREE", 4: "FOUR", 5: "FIVE", 6: "SIX",
            7: "SEVEN", 8: "EIGHT", 9: "NINE", 10: "TEN"}

# Ordningen är dramaturgi, inte alfabetisk: liten först, störst sist.
RASER = [("truffle", "TRUFFLE", "POMERANIAN"), ("scout", "SCOUT", "JACK RUSSELL"),
         ("pickle", "PICKLE", "DACHSHUND"), ("pepper", "PEPPER", "BORDER COLLIE"),
         ("dot", "DOT", "DALMATIAN"), ("kelda", "KELDA", "SIBERIAN HUSKY"),
         ("rufus", "RUFUS", "GOLDEN RETRIEVER"), ("bruno", "BRUNO", "SAINT BERNARD")]
KLIENT = {r: (g, t) for r, g, t in rd.rasklient()}


def brus(n):
    n = (n * 1103515245 + 12345) & 0x7FFFFFFF
    return (n >> 16) & 0x7FFF


def bygg_ang():
    """Ängen ritas EN gång och kopieras per ruta. Att bygga om den för varje
    bildruta är tusen gånger samma arbete."""
    B, horisont = 16, int(H * 0.42)
    img = []
    for y in range(H):
        k = min(1.0, y / horisont)
        img.append([(int(96 + 92 * k), int(156 + 62 * k), int(226 + 16 * k), 255)] * W)
    img = [list(r) for r in img]

    def rita(x0, y0, w, h, c):
        for y in range(int(y0), int(y0 + h)):
            for x in range(int(x0), int(x0 + w)):
                if 0 <= y < H and 0 <= x < W:
                    img[y][x] = c
    for i, (cx, cy, bredd) in enumerate([(2, 2, 6), (16, 1, 4), (24, 3, 5)]):
        for b in range(bredd):
            rita((cx + b) * B, (cy + (b % 2)) * B, B, (1 + brus(i * 13 + b) % 2) * B,
                 (248, 251, 255, 255))
    for bx in range(0, W // B + 1):
        rita(bx * B, horisont - B - (brus(bx * 7) % 2) * (B // 2), B, 3 * B, (78, 118, 52, 255))
    GRAS = [(106, 152, 62), (98, 143, 58), (114, 160, 66), (90, 134, 54)]
    for by, y in enumerate(range(horisont, H, B)):
        for bx, x in enumerate(range(0, W, B)):
            n = brus(bx * 31 + by * 17)
            f = 0.9 + min(0.2, by * 0.03)
            rita(x, y, B, B, tuple(min(255, int(v * f)) for v in GRAS[n % 4]) + (255,))
            if n % 5 == 0:
                rita(x + (n % 11), y + 2, 2, B // 3, (128, 176, 74, 255))
    return img


ANG = None
LOGGA = None


def duk():
    global ANG
    if ANG is None:
        ANG = bygg_ang()
    return [list(r) for r in ANG]


def morkt():
    ut = []
    for y in range(H):
        k = y / H
        ut.append([(int(18 + 16 * k), int(24 + 20 * k), int(16 + 12 * k), 255)] * W)
    return [list(r) for r in ut]


def hund(img, rasid, cx, fot, hojd, yaw, t=None, bar=0, halsband=0):
    """En hund klistrad på duken, med skuggan där tassarna FAKTISKT landar.

    Fotlinjen mäts i spriten i stället för att antas — en tax fyller inte rutan
    som en bernhardshund, och ett antaget värde gav skuggor som låg fel för
    halva uppsättningen."""
    geoid, tex = KLIENT[rasid]
    pose = mv.walk_pose(t) if t is not None else {}
    src = rd.rita(geoid, tex, 260, 260, yaw=yaw, pitch=9, pose=pose, bar=bar,
                  halsband=halsband, bakgrund=NYCKEL)
    nyckl = [[(p[0], p[1], p[2], 0 if p[:3] == NYCKEL[:3] else 255) for p in rad]
             for rad in src]
    nedersta = max((y for y in range(260) if any(p[3] for p in nyckl[y])), default=240)
    fot_y = fot - hojd + int(hojd * (nedersta + 1) / 260)
    for i, (bredd, m) in enumerate(((0.62, 0.80), (0.44, 0.64))):
        b = int(hojd * bredd)
        for y in range(fot_y - i, fot_y - i + 3 - i):
            for x in range(cx - b // 2, cx + b // 2):
                if 0 <= y < H and 0 <= x < W:
                    p = img[y][x]
                    img[y][x] = (int(p[0] * m), int(p[1] * m), int(p[2] * m), 255)
    # paste() CENTRERAR på sitt y-argument — den ställer inte fötterna där. Med
    # fotlinjen inskickad rakt av hamnade halva hunden nedanför duken, och i
    # röksrutorna såg de ut att vara små och sitta på nedre kanten. Exakt samma
    # fälla som hjältebilden gick i.
    mv.paste(img, nyckl, 260, 260, cx, fot - hojd // 2, hojd)


def text(img, s, cx, y, skala, farg=(240, 244, 250, 255)):
    """Kontur åt åtta håll. Vit text mot ljus himmel går annars inte att läsa,
    och en enkel slagskugga räcker inte när bakgrunden är ljus åt alla håll."""
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)):
        mv.text(img, s, cx + dx, y + dy, skala, (12, 16, 22, 255))
    mv.text(img, s, cx, y, skala, farg)


def stampel(img):
    mv.text(img, "LOYAL.PELLEOPS.SE", W - 62, H - 10, 1, (150, 170, 130, 255))
    return img


def toning(img, i, n, kant=8):
    k = min(1.0, (i + 1) / kant, (n - i) / kant)
    if k >= 1.0:
        return img
    return [[(int(p[0] * k), int(p[1] * k), int(p[2] * k), 255) for p in rad] for rad in img]


def scener():
    ut = []
    ut += [("titel", i, 75) for i in range(75)]
    for ri in range(len(RASER)):
        ut += [("ras", ri, i, 60) for i in range(60)]
    ut += [("apport", i, 105) for i in range(105)]
    for f in range(1, 9):
        ut += [("halsband", f, i, 12) for i in range(12)]
    ut += [("valp", i, 75) for i in range(75)]
    ut += [("flock", i, 90) for i in range(90)]
    ut += [("slut", i, 120) for i in range(120)]
    return ut


def ruta(job):
    global LOGGA
    sort = job[0]
    if sort == "titel":
        _, i, n = job
        img = morkt()
        if LOGGA is None:
            LOGGA = rr.read_png(f"{BASE}/publish/logo.png")
        lw, lh, lp = LOGGA
        mv.paste(img, [[(p[0], p[1], p[2], 255) for p in r] for r in lp], lw, lh,
                 W // 2, 74, 118)
        text(img, "LOYAL COMPANIONS", W // 2, 168, 3)
        text(img, f"{RAKNEORD[len(RASER)]} HAND-MADE DOGS FOR MINECRAFT BEDROCK",
             W // 2, 208, 1, (188, 214, 160, 255))
        return toning(img, i, n)
    if sort == "ras":
        _, ri, i, n = job
        rasid, namn, ras = RASER[ri]
        img = duk()
        hund(img, rasid, W // 2, int(H * 0.88), 190, 18 + i * 0.9, t=i / FPS,
             halsband=(ri % 8) + 1)
        text(img, namn, W // 2, H - 42, 2)
        text(img, ras, W // 2, H - 22, 1, (196, 220, 170, 255))
        return toning(stampel(img), i, n)
    if sort == "apport":
        _, i, n = job
        img = duk()
        # bollen flyger ut, hunden springer efter, kommer tillbaka med den
        t = i / n
        if t < 0.30:
            bx = int(W * (0.5 + 1.2 * t))
            by = int(H * 0.62 - math.sin(t / 0.30 * math.pi) * 60)
            for y in range(by - 4, by + 4):
                for x in range(bx - 4, bx + 4):
                    if 0 <= y < H and 0 <= x < W and (x - bx) ** 2 + (y - by) ** 2 < 14:
                        img[y][x] = (196, 72, 72, 255)
            hund(img, "rufus", int(W * 0.32), int(H * 0.88), 185, 34, t=i / FPS)
            text(img, "THROW IT", W // 2, H - 34, 2)
        elif t < 0.62:
            k = (t - 0.30) / 0.32
            hund(img, "rufus", int(W * (0.30 + 0.45 * k)), int(H * 0.88), 185, 82,
                 t=i / FPS)
            text(img, "THEY GO AND GET IT", W // 2, H - 34, 2)
        else:
            k = (t - 0.62) / 0.38
            hund(img, "rufus", int(W * (0.75 - 0.35 * k)), int(H * 0.88), 185, 262,
                 t=i / FPS, bar=1)
            text(img, "AND BRING IT BACK", W // 2, H - 34, 2)
        return toning(stampel(img), i, n)
    if sort == "halsband":
        _, farg, i, n = job
        img = duk()
        hund(img, "dot", W // 2, int(H * 0.88), 195, 20, halsband=farg)
        text(img, "COLLARS IN EIGHT COLOURS", W // 2, H - 34, 1)
        return stampel(img)
    if sort == "valp":
        _, i, n = job
        img = duk()
        hund(img, "kelda", int(W * 0.38), int(H * 0.88), 190, 22, t=i / FPS)
        hund(img, "kelda", int(W * 0.66), int(H * 0.88), 96, 26, t=i / FPS + 0.4)
        text(img, "AND THEY HAVE PUPPIES", W // 2, H - 34, 2)
        return toning(stampel(img), i, n)
    if sort == "flock":
        _, i, n = job
        img = duk()
        # hela flocken travar förbi, bakre raden mindre och först ritad
        # BAKRE RADEN MÅSTE SYNAS FÖRBI DEN FRÄMRE. Först stod de på samma
        # x-linjer och bara tjugo bildpunkter högre upp — de försvann helt
        # bakom framraden och scenen visade tre hundar i stället för sex.
        for rasid, fx, fot, hojd, fas in (("pickle", 0.11, 0.62, 104, 0.0),
                                          ("scout", 0.40, 0.60, 98, 0.5),
                                          ("dot", 0.69, 0.62, 106, 1.0),
                                          ("bruno", 0.24, 0.96, 200, 0.2),
                                          ("rufus", 0.56, 0.98, 190, 0.7),
                                          ("truffle", 0.86, 0.96, 160, 1.2)):
            hund(img, rasid, int(W * fx), int(H * fot), hojd, 16 + i * 0.35,
                 t=i / FPS + fas)
        text(img, "FETCH . COMMANDS . COLLARS . PUPPIES", W // 2, H - 26, 1)
        return toning(stampel(img), i, n)
    if sort == "slut":
        _, i, n = job
        img = morkt()
        text(img, "LOYAL COMPANIONS", W // 2, 62, 3)
        text(img, "LOYAL.PELLEOPS.SE", W // 2, 128, 2, (196, 220, 170, 255))
        text(img, "CURSEFORGE . MCPEDL SOON", W // 2, 168, 1)
        text(img, "MINECRAFT BEDROCK", W // 2, 208, 1, (150, 170, 130, 255))
        return toning(img, i, n, kant=15)
    raise ValueError(sort)


def arbetare(arg):
    idx, job = arg
    rr.write_png(f"{UTKAT}/{idx:05d}.png", W, H, ruta(job))
    return idx


def gif():
    """Sajtens och README:s loopande snutt. Kattprojektets gif var handgjord en
    gång och visade fyra katter långt efter att det blivit sex — här är den ett
    byggsteg, så den kan inte bli gammal."""
    palett = "/tmp/loyal-gif-palett.png"
    filt = f"fps=12,scale={W}:-1:flags=neighbor"
    for steg in (["-vf", f"{filt},palettegen=max_colors=192", palett],
                 ["-i", palett, "-lavfi", f"{filt}[x];[x][1:v]paletteuse=dither=none",
                  "-loop", "0", GIF]):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                        "-i", f"{UTKAT}/%05d.png"] + steg, check=True)
    print(f"  {GIF} ({os.path.getsize(GIF) // 1024} kB)")


def main():
    jobb = scener()
    if SMOKE:
        jobb = jobb[::25]
    shutil.rmtree(UTKAT, ignore_errors=True)
    os.makedirs(UTKAT)
    print(f"{len(jobb)} rutor à {W}x{H}, {multiprocessing.cpu_count()} kärnor")
    with multiprocessing.Pool(min(5, multiprocessing.cpu_count())) as pool:
        for k, _ in enumerate(pool.imap_unordered(arbetare, list(enumerate(jobb)),
                                                  chunksize=8)):
            if k % 100 == 0:
                print(f"  {k}/{len(jobb)}")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                    "-i", f"{UTKAT}/%05d.png", "-vf", "scale=1920:1080:flags=neighbor",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", MP4],
                   check=True)
    print(f"klar: {MP4} ({len(jobb) / FPS:.1f} s, {os.path.getsize(MP4) // 1024} kB)")
    gif()


if __name__ == "__main__":
    main()
