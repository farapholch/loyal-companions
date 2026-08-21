# Loyal Companions

Minecraft **Bedrock** add-on: hand-made dogs to tame, train and take with you.
Sibling project to [Purrfect Companions](https://purrfect.pelleops.se) — same
machinery, other animal.

## The dogs

Four dogs, chosen so you can tell them apart in half a second: they differ in
**size, colour and silhouette** at the same time. One light, one dark, one
cool-toned, one small and fluffy.

| Entity | Name | Breed | Look | Scale | Lives in |
|---|---|---|---|---|---|
| `hund:truffle` | Truffle | Pomeranian | Dark sable with tan legs and a bushy tail over her back | 0.68 | plains |
| `hund:rufus` | Rufus | Golden Retriever | Warm gold with cream legs | 1.05 | forest |
| `hund:kelda` | Kelda | Siberian Husky | Silver-grey and white, blue eyes | 1.00 | taiga |
| `hund:pepper` | Pepper | Border Collie | Black with a white chest and white paws | 0.95 | plains |

Tame them with **bones** — a third of the time per bone, so it costs a few.

Truffle is **Truffle** in the family build, the way the cats carry their real
names there. She has her own geometry (`geometry.hund_ludd`): the base model
plus a neck ruff and a bushy tail. A Pomeranian scaled down from a guard dog
is just a wolf puppy; the fluff is what makes her a Pomeranian.

## What is planned

**Fetch and commands** is the core the pack is being built around: throw a
stick and the dog brings it back, plus sit, stay, follow and seek. That is the
first thing anyone tries with a dog, and vanilla has none of it.

## How it is built

Nothing is drawn or written by hand that can be computed from a table.

| Script | Owns |
|---|---|
| `tools/make_dogs.py` | Entities, client definitions, coats, spawn eggs, spawn rules, language |
| `tools/loyal-test` | JSON and PNG validation, structure checks, a real Bedrock server run |

The geometry is the guard dog built for Purrfect Companions — our first
four-legged model, already verified, and no reason to invent it twice. The
coats are recoloured from its texture, so every breed shares exactly the UV
layout the geometry expects.

`tools/loyal-test` shares the Bedrock server lock (`/tmp/bds.lock`) with the
cat project: one server at a time, or they collide on the ports.

### Traps already paid for

- A dog summoned at y=20 in the test world dies within a second — it is not
  flat ground there. The failure reads as "taming does not work" (0/3) when it
  is really "the animal is gone". The test carves a floor and an air pocket.
- The breed list is read from the pack, never written twice. Peach was added
  and silently not tested — the line still said "3/3" and looked green. The
  cat project fell into that exact trap three times.
- A here-document terminator must stand alone on its line: `PY)` is not a
  terminator, and bash silently swallowed the rest of the file.
