# Changelog

## 1.3.0

**Hundarna såg ut som stående figurer i spelet.** Pelles skärmbilder visade
det jag aldrig hade tittat på: rakt framifrån, vyn man möter när en hund
springer emot en. Alla mina egna bilder var trekvartsvy, och i trekvart döljs
precis det som var fel.

- **Proportionerna.** Kroppens framsida var lika hög som bred och stod på lika
  höga ben — en smal pelare på fjorton enheter. Kroppen är nu lägre, benen
  kortare och huvudet större, och det sitter ner i bringan i stället för att
  balansera ovanpå ryggen.
- **Nospartiet** var nästan lika brett som huvudet och nosen täckte det mesta
  av det. Ansiktet läste som en skärm med en svart platta. Nu smalare nosparti,
  liten nostipp och plats åt ögonen ovanför.
- **Ögonen syntes inte** på enfärgade hundar — ett brunt öga i brun päls är
  ingenting. Varje öga har nu en kontrastfläck som går åt motsatt håll mot
  pälsen.
- **Bringan** var en vit rektangel över hela framsidan och såg ut som ett
  förkläde. Nu en smal kil som smalnar av nedåt.
- **Detaljer i ansiktet ritas i hela pixlar.** Ritfunktionen rundar utåt i båda
  ändar, så en nostipp på 2x1,5 pixlar blev 3x2 — nästan dubbelt så stor.

`tools/render_dogs.py --framifran` finns nu, så vyn aldrig mer är ogranskad.

## 1.2.1

Ingen ny funktion — tre saker som var otestade är det inte längre:

- **En riktig klient ansluter nu i testkedjan.** Den ser paketet som en
  spelares spel gör: alla tio egna föremål finns i klientens item_registry,
  visslan går att ge och hamnar i inventariet, hundarna strömmas in med rätt
  typnamn, och **egenskaperna synkas till klienten**. Det sista är det
  halsbandet och bollen i munnen hänger i — `part_visibility` läser dem på
  klientsidan, och att servern sätter dem bevisar ingenting om att klienten
  får veta det.
- **Tillståndet överlever en omstart.** Tamflagga, kommandoläge, halsbandsfärg,
  buret föremål och dess dynamiska egenskap läses tillbaka intakta efter att
  servern startats om mot samma värld. Det stod som ett påstående i en
  kommentar och var aldrig mätt.
- **Trettioen hundar kostar 0,09 ms per loopvarv** mot en tickbudget på 50 ms.
  Loopen mäter sig själv; `tools/loyal-uthallighet` kör provet.

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
