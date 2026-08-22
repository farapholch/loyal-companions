#!/bin/bash
# Publicerar sajten (loyal.pelleops.se, nginx :8093).
#
# SAJTEN ERBJUDER INGEN NEDLADDNING. Paketet ska hämtas från CurseForge eller
# MCPEDL, inte härifrån — därför bygger det här skriptet inget .mcaddon och
# kopierar inget. Leveransen sköts av tools/loyal-ship.
#
# Sidorna bor i site/, bilderna genereras av tools/make_promo.py,
# tools/make_logo.py och tools/render_dogs.py.
set -e
SRC=/opt/loyal-companions
DEST=/var/www/loyal
VERSION=$(python3 -c "import json;print('.'.join(map(str,json.load(open('$SRC/LoyalCompanions_BP/manifest.json'))['header']['version'])))")

mkdir -p "$DEST"

# SIDORNA SPEGLAS, inte bara kopieras. Tas en sida bort ur site/ ligger den
# annars kvar publikt för alltid — en död sida som ingen länkar till men som
# gamla länkar och sökmotorer hittar.
for GAMMAL in "$DEST"/*.html; do
  [ -e "$GAMMAL" ] || continue
  [ -f "$SRC/site/$(basename "$GAMMAL")" ] || { echo "   tar bort $(basename "$GAMMAL")"; rm -f "$GAMMAL"; }
done
cp "$SRC"/site/*.html "$DEST/"

# BARA BILDERNA SIDAN ANVÄNDER. publish/ innehåller också enstaka
# felsökningsrenderingar, och de har inget på en publik sajt att göra.
for BILD in logo.png hero.png dogs.png favicon.png apple-touch-icon.png pack_icon.png; do
  cp "$SRC/publish/$BILD" "$DEST/"
done

# INGEN .mcaddon PÅ SAJTEN. Ligger det en kvar sedan tidigare tas den bort — en
# gammal fil som fortfarande går att hämta är värre än ingen fil alls.
find "$DEST" -maxdepth 1 -name "*.mcaddon" -printf "   tar bort %f\n" -delete

# Versionsnumret på sidan hängde kvar i fem releaser i kattprojektet när det
# redigerades för hand — sidan bär en platshållare i stället, som fylls i här.
sed -i "s/__VERSION__/$VERSION/g" "$DEST/index.html"

# CACHEN. Cloudflare håller bilder i fyra timmar och vi har ingen token att
# rensa med, så en ny hjältebild syns inte förrän TTL:en löpt ut. Versionsstämpla
# länkarna i stället: samma fil, ny URL vid varje release.
sed -i -E "s/(src=\"[^\"]+\.png)\"/\1?v=$VERSION\"/g" "$DEST/index.html"

chmod 644 "$DEST"/* 2>/dev/null || true
echo "publicerat v$VERSION till $DEST (https://loyal.pelleops.se)"
