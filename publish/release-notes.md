# Release notes (English — the source for store release notes)

CHANGELOG.md är projektets egen logg och är på svenska. Butikssidan är på
engelska, och en svensk release-not där är fel språk för läsaren. Den här
filen är vad tools/loyal-ship skickar till CurseForge.

## 1.4.0

**The eight dogs are different to use now.** Until today they had the same
health, the same speed, the same bite and the same hitbox — they differed only
in the size of the model and the coat. The models really are built from each
breed's own measurements, but a Saint Bernard ran as fast and bit as hard as a
Jack Russell.

Now each breed connects to something the pack already did:

- **Bruno** the Saint Bernard: 26 health, the hardest bite, the slowest walk
- **Scout** the Jack Russell: the fastest, and the easiest to hurt
- **Pickle** the dachshund digs **twice as often** as anyone else, because a
  dachshund is bred to dig
- **Rufus** the retriever fetches from 24 blocks, against 10 for the shortest
  reach
- **Truffle** the Pomeranian senses a threat at 20 blocks where Bruno needs 12 —
  small watchdogs hear it first

The hitbox follows the dog's size as well. It was the same for all eight, so a
Pomeranian was as wide to walk into as a Saint Bernard.

You pick a dog for the job now, not for the coat.

## 1.3.0

Dogs looked like standing figures in game — the body's front was as tall as it
was wide, on legs just as tall, which head-on reads as a column rather than a
four-legged animal. Fixed by rebuilding the proportions from the front view:

- Lower body, shorter legs, a bigger head that sits down in the chest instead
  of balancing on the back.
- Narrower muzzle with a small nose. It used to cover most of the face, and
  the whole head read as a screen with a black plate on it.
- Eyes now have a contrast patch behind them, so they are visible on
  single-coloured dogs. A brown eye in brown fur is nothing at all.
- The chest marking was a white rectangle across the whole front and looked
  like an apron. Now a narrow wedge.

## 1.2.1

No new features. Three things that were untested no longer are: a real Bedrock
client now connects as part of the release chain and checks that the custom
items reach the client, that dogs stream in correctly and that entity
properties sync — the chain the collar and the ball in the mouth are drawn by.
State (tame flag, command mode, collar colour, carried item) is proven to
survive a server restart, and thirty-one dogs cost 0.09 ms per script pass.

## 1.2.0

Five behaviour fixes found by reviewing what the pack does rather than what
its files say:

- **Stay now means stay.** Fetch switched on regardless of command, and
  picking up moves the dog — so a dog told to stay wandered off the moment
  someone dropped a stick within sixteen blocks.
- Puppies could be born full-sized.
- Wild dogs never despawned.
- Two behaviours shared a priority, which is undefined in Bedrock; a sitting
  guard dog was a lottery.
- Barking every thirteen seconds per dog, and five breeds crowding the plains.

Dogs also work in the Nether and the End now — fetch, whistle and digging were
overworld-only.

## 1.1.0

Swedish is actually Swedish now: breed names, items and every message. The dog
whistle was missing its name in the language file. Engine requirement raised to
1.20.50, which is what the pack's own files declare.

## 1.0.0

First release. Eight dogs — Truffle, Rufus, Kelda, Pepper, Pickle, Bruno, Dot
and Scout — each with its own body and coat pattern. Fetch, command modes, dog
whistle, collars in eight colours, puppies, digging, guard growling, and voices
pitched by size.
