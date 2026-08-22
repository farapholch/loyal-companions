#!/bin/bash
# Publicerar sajten (loyal.pelleops.se, nginx :8093).
#
# Sidan bor i site/index.html; bilderna genereras av tools/make_promo.py,
# tools/make_logo.py och tools/render_dogs.py. Nedladdningsfilen byggs HÄR, via
# leveranskedjan, så den fil besökarna får alltid är en som passerat testet och
# namngranskningen — en handkopierad .mcaddon är en publik fil ingen kontrollerat.
set -e
SRC=/opt/loyal-companions
DEST=/var/www/loyal
VERSION=$(python3 -c "import json;print('.'.join(map(str,json.load(open('$SRC/LoyalCompanions_BP/manifest.json'))['header']['version'])))")

if [ "${1:-}" != "--no-build" ]; then
  "$SRC/tools/loyal-ship" --public --no-upload
fi
ADDON="/tmp/loyal-companions-v$VERSION.mcaddon"
[ -f "$ADDON" ] || { echo "AVBRYTER: $ADDON finns inte — kör utan --no-build"; exit 1; }

# SISTA SPÄRREN FÖRE PUBLIK YTA. loyal-ship granskar redan sitt eget bygge, men
# den här filen kan ha kommit någon annanstans ifrån, och sajten är publik.
NAMN=$(python3 - "$SRC" <<'PY'
import json, os, sys
pf = f"{sys.argv[1]}/variants.private.json"
ut = set()
if os.path.exists(pf):
    for cfg in json.load(open(pf, encoding="utf-8")).values():
        for slug, disp in (cfg.get("names") or {}).values():
            ut |= {slug, disp}
print("|".join(sorted(ut)) or "___aldrig___")
PY
)
if unzip -qq -p "$ADDON" 2>/dev/null | grep -qiE "$NAMN"; then
  echo "AVBRYTER: $(basename "$ADDON") innehåller privata namn"; exit 1
fi

mkdir -p "$DEST"
# SIDORNA SPEGLAS, inte bara kopieras. Tas en sida bort ur site/ ligger den
# annars kvar publikt för alltid — en död sida som ingen länkar till men som
# sökmotorer och gamla länkar hittar.
for GAMMAL in "$DEST"/*.html; do
  [ -e "$GAMMAL" ] || continue
  [ -f "$SRC/site/$(basename "$GAMMAL")" ] || { echo "   tar bort $(basename "$GAMMAL")"; rm -f "$GAMMAL"; }
done
cp "$SRC"/site/*.html "$DEST/"
# BARA BILDERNA SIDAN ANVÄNDER. publish/ innehåller också enstaka
# felsökningsrenderingar (dog-*.png), och de har inget på en publik sajt att göra.
for BILD in logo.png hero.png dogs.png favicon.png apple-touch-icon.png pack_icon.png; do
  cp "$SRC/publish/$BILD" "$DEST/"
done
cp "$ADDON" "$DEST/loyal-companions-v$VERSION.mcaddon"
# äldre versioner städas bort, annars växer katalogen med varje släpp
find "$DEST" -maxdepth 1 -name "*.mcaddon" ! -name "loyal-companions-v$VERSION.mcaddon" -delete

# Nedladdningslänken hängde kvar på en gammal version i fem releaser i
# kattprojektet när den redigerades för hand — sidan bär en platshållare i
# stället, som fylls i här.
sed -i "s/__VERSION__/$VERSION/g" "$DEST/index.html"

# CACHEN. Cloudflare håller bilder i fyra timmar och vi har ingen token att
# rensa med, så en ny hjältebild syns inte förrän TTL:en löpt ut — sajten
# visade gamla bilder i timmar efter varje släpp utan att något var fel med
# filerna. Versionsstämpla länkarna i stället: samma fil, ny URL vid varje
# release, och besökarna behåller nyttan av cachen däremellan.
sed -i -E "s/(src=\"[^\"]+\.png)\"/\1?v=$VERSION\"/g" "$DEST/index.html"

chmod 644 "$DEST"/* 2>/dev/null || true
echo "publicerat v$VERSION till $DEST (https://loyal.pelleops.se)"
