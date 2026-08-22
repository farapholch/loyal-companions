# Loyal Companions

Minecraft **Bedrock** add-on: eight hand-made dogs to tame, train and take with
you. Sibling project to [Purrfect Companions](https://purrfect.pelleops.se) —
same machinery, other animal.

**[loyal.pelleops.se](https://loyal.pelleops.se)** — download and screenshots.

![the dogs](publish/hero.png)

## The dogs

Eight dogs you can tell apart in half a second, because they differ in **size,
colour and silhouette at the same time**. The body is computed from
measurements — leg height, body length, head size, ear shape — so a dachshund
really is low and long and a Saint Bernard really is heavy. Four coloured
copies of one model looked identical from across a field; that is what this
replaced.

| Entity | Name | Breed | Build | Scale | Lives in |
|---|---|---|---|---|---|
| `hund:truffle` | Truffle | Pomeranian | ruff and a bushy tail | 0.68 | plains |
| `hund:rufus` | Rufus | Golden Retriever | hanging ears, cream chest | 1.05 | forest |
| `hund:kelda` | Kelda | Siberian Husky | dark mask, blue eyes, white socks | 1.00 | taiga |
| `hund:pepper` | Pepper | Border Collie | black with a white blaze | 0.95 | plains |
| `hund:pickle` | Pickle | Dachshund | short legs, long body, long ears | 0.80 | plains |
| `hund:bruno` | Bruno | Saint Bernard | tall, broad, heavy head | 1.20 | extreme hills |
| `hund:dot` | Dot | Dalmatian | white with spots | 1.00 | plains |
| `hund:scout` | Scout | Jack Russell Terrier | small, tan saddle | 0.75 | plains |

Tame them with **bones** — a third of the time per bone, so it costs a few.

## What they do

**Fetch.** Throw the Fetch Ball (wool ring + slime ball) — or just a stick or a
bone — and the dog runs after it, picks it up and brings it back to your hand.
It carries what it fetched visibly in its mouth.

**Take commands.** Right-click your dog with a bone to cycle **Follow → Stay →
Guard**. Guard dogs attack monsters that come near you, growl a warning when
something is close, and stay within a longer leash.

**Come when called.** The Dog Whistle (iron ingot + bone) calls every dog of
yours within 96 blocks and puts them back into Follow. It is the way out of a
Stay command you forgot about three valleys ago.

**Wear a collar.** Right-click with any of eight dyes to put a collar on your
dog, so you can tell your two border collies apart.

**Dig things up.** Every few minutes, when you are watching, a dog digs up
something — usually a bone or a bit of string, occasionally a nugget, rarely an
emerald.

**Eat, heal, breed.** Any meat heals them. Two tame, healthy dogs of the same
breed fed steak produce a puppy, and the puppy is born already yours.

**Sound like dogs.** Pitch follows size: the Pomeranian yaps and the Saint
Bernard rumbles.

## How it is built

Nothing is drawn or written by hand that can be computed from a table.

| Script | Owns |
|---|---|
| `tools/make_dogs.py` | Geometries, coats, entities, client definitions, spawn eggs, spawn rules, render controller, sounds, items, language |
| `tools/render_dogs.py` | Preview renders straight from the pack's own files |
| `tools/make_promo.py` | Pack icon and store hero image |
| `tools/loyal-test` | JSON and PNG validation, structure checks, a real Bedrock server run, and a real client connecting over the network |
| `tools/loyal-uthallighet` | What only shows over time and scale: does the state survive a restart, what does the loop cost with thirty dogs |
| `tools/make_logo.py` | The framed 512×512 logo the pack icon is derived from |
| `tools/loyal-ship` | Build → test → package → Mod Mate, refuses to send a failing build |
| `publish_site.sh` | Publishes loyal.pelleops.se, and builds the download it publishes |
| `make_variant.py` | Public build vs the family build; private names never enter the repo |

`tools/loyal-test` shares the Bedrock server lock (`/tmp/bds.lock`) with the cat
project: one server at a time, or they collide on the ports.

### Traps already paid for

- **`minecraft:behavior.pickup_items` alone does nothing.** A dog with the
  behaviour — in a component group, in the base components, tamed, untamed,
  with and without `minecraft:equippable` — never walked to the ball. A fox in
  the same test world took the same ball every time. The difference is
  **`minecraft:shareables`**, the mob's wishlist: without it there is no item
  worth walking to. Eight server runs.
- **Vanilla destroys what the mob picks up.** There is nowhere to put it:
  `minecraft:equippable` does not even register on this entity, and a mounted
  `minecraft:inventory` stayed empty. The script therefore owns the carry — it
  removes the ball just before vanilla gets there and sets `hund:bar`. It
  cannot always win that race, so an item that vanishes while the dog is
  standing on it counts as fetched too.
- **A dog summoned at y=20 in the test world dies within a second.** The
  failure reads as "taming does not work" (0/3) when the animal is simply gone.
  The test carves a floor and an air pocket — and the pocket must be big enough
  for whatever the test does inside it: a fetch test that drops the ball eight
  blocks away needs eight blocks of floor.
- **Hard-coded lists go stale.** The breed list is read from the pack, never
  written twice. `APPORTBARA` exists in both the generator and the script
  because the script cannot read entity JSON — so the test compares them.
- **Invisible ears.** One unit thick in the coat colour: the golden retriever
  looked like a wolf. Nothing in any log says so. `tools/render_dogs.py` exists
  because the only other way to find that out is to ship it.
- **A text replacement takes the first match.** The digging code was inserted
  into the whistle function instead of the main loop; the reference error
  vanished into a `catch` and the symptom was "the whistle does not bring the
  dog home".
- **`"mountain"` and `"forest"` are both real biome tags, `"mountains"` is
  not.** A wrong tag means a breed that simply never appears, silently. The
  test checks them against vanilla's biome definitions — not against vanilla's
  spawn rules, which use only a handful of them.
- **Two goals with the same priority is undefined.** `stay_while_sitting` and
  `melee_attack` both sat on 5; a sitting guard dog was a lottery. The clash
  only exists in the *combination* of component groups that can be active
  together, so the test checks the combinations, not the groups.
- **`minecraft:persistent` on a wild animal never despawns.** Eight breeds
  that stay forever swell a world year after year. It belongs in the tamed
  group, not in the base components.
- **A command has to survive temptation.** Fetch switched on regardless of
  mode, and `pickup_items` moves the dog — so "stay" lasted until someone
  dropped a stick within sixteen blocks. The test now proves a staying dog
  ignores a ball eight blocks away, and that test was verified by putting the
  bug back and watching it fail.
- **A here-document terminator must stand alone on its line**: `PY)` is not a
  terminator, and bash silently swallows the rest of the file.

### What a real client proves

`tools/testbot/smoke-test.js` connects an actual Bedrock client over the
network. It is the only thing here that sees the pack the way a player's game
does: that all ten custom items reach the client's item registry, that the
whistle can be given and lands in an inventory, that the dogs stream in with
the right type names, and that **entity property syncs flow to the client**.
That last one matters more than it sounds: the collar and the ball in the
mouth are drawn by `part_visibility`, which reads those properties on the
client. The server setting `hund:halsband` proves nothing about the client
being told.

`tools/loyal-uthallighet` covers the other blind spot, time and scale: the
tame flag, command mode, collar colour, carried item and its dynamic property
all survive a server restart (that was a claim in a comment, unverified, until
it was measured), and thirty-one dogs cost 0.09 ms per loop pass against a
50 ms tick budget.

### What is not verified here

The server has no renderer and no audio, so three things are only checked by
eye and ear in the game: that the collar and the ball in the mouth actually
**look** right (the data behind them is now proven to reach the client), that
the sounds play, and that the coats read well on a real screen.
Everything else — spawning, taming, command modes, fetch, puppies, the collar
property, the whistle, digging — is proven by `tools/loyal-test` against a real
Bedrock server on every run.
