# Butikspaket — CurseForge och MCPEDL

Allt som behövs för att lägga upp Loyal Companions. Ingenting här är publicerat;
uppladdningen sker först när du säger till.

## Namn
Loyal Companions

## Summary (en rad)
Eight hand-made dogs that fetch, guard, obey commands and grow up.

## Description

Minecraft has one dog. This adds eight, and gives them something to do.

**Fetch.** Throw the ball — or a stick, or a bone — and your dog runs after it,
picks it up and carries it back to your hand. You can see what it is carrying.

**Commands.** Right-click with a bone to cycle Follow, Stay and Guard. A guard
dog goes for monsters that come near you and growls when something is close. A
staying dog stays, even when there is a ball in front of it.

**A whistle that works.** Every dog of yours within 96 blocks comes running and
goes back to following you. No more searching for the one you left behind.

**Eight breeds you can tell apart.** A Pomeranian, a golden retriever, a husky,
a border collie, a dachshund, a Saint Bernard, a dalmatian and a Jack Russell.
They are not reskins: each body is built from its own measurements, so the
dachshund really is low and long and the Saint Bernard really is heavy. Tame
them with bones.

**Collars in eight dye colours.** Right-click with a dye, so you can tell your
two border collies apart.

**Puppies.** Feed two tame dogs of the same breed and you get a puppy, born
already yours. It grows up.

**They dig things up.** Bones, string, the odd nugget, once in a long while an
emerald.

**They sound like dogs.** Pitch follows size: the Pomeranian yaps, the Saint
Bernard rumbles.

Made by hand and loaded into a real Bedrock server before every release, which
spawns and tames every breed, throws a ball and checks that the dog comes back
with it.

## Kategori och taggar
Kategori: Addons → Mobs
Taggar: dogs, pets, mobs, animals, fetch, tameable, companions, survival

## Bilder som ska laddas upp

| Fil | Format | Används till |
|---|---|---|
| `publish/logo.png` | 512x512 | projektavatar (CurseForge kräver kvadrat, minst 400x400) |
| `publish/hero.png` | 1280x720 | första skärmbilden |
| `publish/store-dogs.png` | 1280x720 | andra skärmbilden, alla åtta med namn |
| `publish/loyal-trailer.mp4` | 1080p, ~35 s | ladda upp på YouTube och klistra in länken i beskrivningen |
| `publish/loyal-trailer.gif` | 480 px, loopar | MCPEDL och andra ställen som tar rörlig bild direkt |

## Filen
Byggs av `tools/loyal-ship --public --no-upload` och hamnar som
`/tmp/loyal-companions-v<version>.mcaddon`. Den PUBLIKA varianten — familjens
hundnamn granskas bort och bygget vägrar packas om ett privat namn finns kvar.

## När projektet finns

1. Skapa projektet på CurseForge (Bedrock → Addons) och fyll i texten ovan.
2. Lägg projekt-ID:t i `.curseforge-project` (bara siffrorna) och API-token i
   `.curseforge-token`. Båda är gitignore:ade.
3. Kör `tools/loyal-ship --curseforge`. Den testar först och vägrar skicka ett
   rött bygge. Utan projekt-ID stannar den direkt.
4. Byt ut "coming soon"-knapparna i `site/index.html` mot riktiga länkar och
   kör `./publish_site.sh`.

MCPEDL tar samma text och samma bilder, men filen laddas upp via deras formulär
— de har inget API.
