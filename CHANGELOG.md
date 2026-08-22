# Changelog

## 1.2.0

Genomgång av beteendet i drift, inte bara av filerna. Fem fynd:

- **Stannakommandot höll inte.** Apportläget slogs på oavsett kommando, och
  eftersom `pickup_items` flyttar hunden gick en hund man beordrat att stanna
  sin väg så fort någon tappat en pinne inom sexton block.
- **Valpar kunde födas fullvuxna.** `minecraft:entity_spawned` la på
  `hund:vuxen` innan parningens `hund:fodd` la på `hund:valp`, och båda sätter
  `minecraft:scale`. Vilken som vann var odefinierat.
- **Vildhundar despawnade aldrig.** `minecraft:persistent` låg i
  baskomponenterna — åtta raser som blir kvar för alltid sväller en värld år
  efter år. Nu gäller den bara tämjda hundar.
- **Två mål delade prioritet.** `stay_while_sitting` och `melee_attack` låg
  båda på 5, `look_at_player` och vaktlägets `follow_owner` båda på 8. Två mål
  med samma siffra är odefinierat i Bedrock; en sittande vakthund var ett
  lotteri.
- **För mycket ljud och för många hundar.** Skällintervallet var 7 s (var
  trettonde sekund per hund), och fem raser i plains gav samlad spawnvikt 15 —
  nästan dubbelt mot vaniljas varg. Nu 20 s respektive vikt fördelad efter hur
  många raser som delar biomet.

Dessutom: skriptet arbetar nu i alla tre dimensionerna. En hund man tagit med
sig till Nether tappade apport, vissla och grävande utan att något sa ifrån.
Och vaktmorrandet hade tjugo sekunders paus, inte två minuter — samma misstag
som kattpaketets "your cat bristles", i hundform.

## 1.1.0

- **Svenska på riktigt.** `sv_SE.lang` innehöll engelsk text ordagrant kopierad
  från `en_US` — paketet lovade svenska i `languages.json` och levererade inte.
  Nu är allt översatt: rasnamnen (Tax, Sankt bernhardshund, Dalmatiner),
  föremålen (Apportboll, Hundvissla) och alla meddelanden.
- **Hundvisslan saknade sitt namn** i språkfilen. Föremålets egen
  `minecraft:display_name` räddade den på engelska, men bara där.
- **Motorkravet höjt till 1.20.50.** Manifestet bad om 1.20.0 medan
  entiteterna deklarerar format 1.20.50 — paketet begärde en motor som inte
  kan läsa dess egna filer.

## 1.0.0

Första utgåvan. Åtta hundar (Truffle, Rufus, Kelda, Pepper, Pickle, Bruno, Dot,
Scout) med egna kroppar och pälsmönster. Apport, kommandolägen, hundvissla,
halsband i åtta färger, valpar, grävande, vaktmorrande och röster med tonhöjd
efter storlek.
