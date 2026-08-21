#!/usr/bin/env python3
"""Bygger en variant av Loyal Companions som en transformerad KOPIA av källan.

Källan är alltid den PUBLIKA versionen — Truffle, Rufus, Kelda och de andra.
Familjens riktiga hundnamn finns bara i variants.private.json, som är
gitignore:ad, och appliceras vid paketering. Privata namn ska aldrig finnas i
repot och aldrig i en publik fil.

VARIANTERNA HAR OLIKA PACK-UUID. Två paket med samma UUID krockar i Minecraft;
den ena skriver tyst över den andra i paketlistan.

    python3 make_variant.py private /tmp/bygge     # → /tmp/bygge/{BP,RP}
    python3 make_variant.py public  /tmp/bygge
"""
import json, os, re, shutil, sys, glob

BASE = os.path.dirname(os.path.abspath(__file__))
PACKS = ("LoyalCompanions_BP", "LoyalCompanions_RP")


def build(variant, outdir):
    cfgs = json.load(open(f"{BASE}/variants.json"))
    pf = f"{BASE}/variants.private.json"
    if os.path.exists(pf):
        cfgs.update(json.load(open(pf, encoding="utf-8")))
    if variant not in cfgs:
        raise SystemExit(f"varianten '{variant}' saknas (privat konfig i variants.private.json?)")
    cfg = cfgs[variant]
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    os.makedirs(outdir)
    for pack in PACKS:
        shutil.copytree(f"{BASE}/{pack}", f"{outdir}/{pack}")

    names = cfg.get("names") or {}
    if names:
        mal = sum((glob.glob(f"{outdir}/**/*.{e}", recursive=True)
                   for e in ("json", "lang", "js")), [])
        for f in mal:
            s = o = open(f, encoding="utf-8").read()
            for src, (slug, disp) in names.items():
                # dc_-PREFIXET FÖRST. \b matchar inte inuti "dc_truffle"
                # (understreck är ett ordtecken), så utan den här raden döps
                # filerna om medan item_texture.json pekar kvar på det gamla
                # namnet → spawnägget blir en rutig "saknad textur".
                s = s.replace(f"dc_{src}", f"dc_{slug}")
                s = re.sub(rf"\b{src}\b", slug, s)
                s = re.sub(rf"\b{src.capitalize()}\b", disp, s)
            if s != o:
                open(f, "w", encoding="utf-8").write(s)
        for src, (slug, _disp) in names.items():
            for p in (f"{outdir}/LoyalCompanions_BP/entities/{src}.json",
                      f"{outdir}/LoyalCompanions_BP/spawn_rules/{src}.json",
                      f"{outdir}/LoyalCompanions_RP/entity/{src}.json",
                      f"{outdir}/LoyalCompanions_RP/textures/entity/{src}.png",
                      f"{outdir}/LoyalCompanions_RP/textures/items/dc_{src}.png"):
                if os.path.exists(p):
                    shutil.move(p, f"{os.path.dirname(p)}/"
                                   f"{os.path.basename(p).replace(src, slug)}")
        raser = cfg.get("breeds", {})
        slugs = "|".join(s for s, _ in names.values())
        for pack in PACKS:
            for spr in ("en_US", "sv_SE"):
                lp = f"{outdir}/{pack}/texts/{spr}.lang"
                rader = [l for l in open(lp, encoding="utf-8").read().rstrip("\n").split("\n")
                         if not re.match(rf"^(entity|item\.spawn_egg\.entity)\.(hund:)?"
                                         rf"({slugs})\.name=", l)]
                for _src, (slug, disp) in names.items():
                    ras = raser.get(slug, "")
                    namn = f"{disp} ({ras})" if ras else disp
                    rader[:0] = [f"entity.hund:{slug}.name={namn}",
                                 f"entity.{slug}.name={namn}",
                                 f"item.spawn_egg.entity.hund:{slug}.name=Spawn {disp}"]
                open(lp, "w", encoding="utf-8").write("\n".join(rader) + "\n")

    bp = json.load(open(f"{outdir}/LoyalCompanions_BP/manifest.json"))
    rp = json.load(open(f"{outdir}/LoyalCompanions_RP/manifest.json"))
    bp["header"]["name"] = cfg["pack_bp"]
    bp["header"]["description"] = cfg["desc_bp"]
    rp["header"]["name"] = cfg["pack_rp"]
    for m in (bp, rp):
        m["metadata"] = {"authors": ["Pellzor"]}
    u = cfg.get("uuids")
    if u:
        bp["header"]["uuid"] = u["bp_header"]
        rp["header"]["uuid"] = u["rp_header"]
        rp["modules"][0]["uuid"] = u["rp_module"]
        for mod in bp["modules"]:
            mod["uuid"] = u["bp_script"] if mod.get("type") == "script" else u["bp_module"]
        for dep in bp.get("dependencies", []):
            if "uuid" in dep:
                dep["uuid"] = u["rp_header"]
    json.dump(bp, open(f"{outdir}/LoyalCompanions_BP/manifest.json", "w"), indent=2)
    json.dump(rp, open(f"{outdir}/LoyalCompanions_RP/manifest.json", "w"), indent=2)
    return ".".join(map(str, bp["header"]["version"])), bp["header"]["uuid"], rp["header"]["uuid"]


if __name__ == "__main__":
    variant = sys.argv[1] if len(sys.argv) > 1 else "public"
    outdir = sys.argv[2] if len(sys.argv) > 2 else f"/tmp/loyal-{variant}"
    ver, bpu, rpu = build(variant, outdir)
    print(f"{variant}: v{ver} → {outdir}")
    print(f"  BP uuid {bpu}")
    print(f"  RP uuid {rpu}")
