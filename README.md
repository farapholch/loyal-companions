# Loyal Companions

Minecraft **Bedrock** add-on: hand-made dogs to tame, train and take with you.
Sibling project to [Purrfect Companions](https://purrfect.pelleops.se) — same
machinery, other animal.

## The dogs

| Entity | Name | Breed | Lives in |
|---|---|---|---|
| `hund:bailey` | Bailey | Golden Retriever | forest |
| `hund:shadow` | Shadow | German Shepherd | plains |
| `hund:kelda` | Kelda | Siberian Husky | taiga |
| `hund:peach` | Peach | Pomeranian | plains |

Tame them with **bones** — a third of the time per bone, so it costs a few.

Names and coats are placeholders for the public variant; the family build
carries real dogs, the way the cats do — Peach is **Truffle** there.

Peach uses her own geometry (`geometry.hund_ludd`): the base model plus a neck
ruff and a bushy tail that lies over her back. A Pomeranian scaled down from a
guard dog is just a wolf puppy; the fluff is what makes her a Pomeranian.

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
