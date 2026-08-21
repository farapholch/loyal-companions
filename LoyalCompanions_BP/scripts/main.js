import { world, system, ItemStack } from "@minecraft/server";

// ---------------------------------------------------------------------------
// Loyal Companions — allt som inte går att uttrycka i entitets-JSON.
//
// APPORTERINGEN är kärnan: kasta bollen, hunden hämtar den och kommer tillbaka
// med den i munnen. Arbetsdelningen mellan vanilla och skript kostade åtta
// serverkörningar att hitta, och den är inte den man gissar:
//
//   VANILLA GÅR DIT. Skript-API:t kan inte sätta ett mål för en entitet, men
//   minecraft:behavior.pickup_items får moben att gå fram till ett föremål.
//   Beteendet ensamt gör dock INGENTING — det som avgör är
//   minecraft:shareables, mobens önskelista. Utan den står hunden kvar hur
//   många varianter av pickup_items man än provar (i grupp, i baskomponenterna,
//   tämjd, otämjd, med och utan equippable). Räven i samma testvärld tog samma
//   boll varje gång, och skillnaden mellan räven och hunden var den listan.
//
//   SKRIPTET BÄR. När moben når fram FÖRSTÖR vanilla föremålet: hunden har
//   ingen ficka att lägga det i (minecraft:equippable registreras inte alls på
//   den här entiteten, och en monterad minecraft:inventory förblev tom).
//   Därför tar skriptet bollen strax innan vanilla hinner — den plockas bort
//   när hunden är inom GRIPAVSTAND och blir egenskapen hund:bar, som
//   renderaren visar som en boll i munnen.
const RADIE = 16;              // hur långt hunden letar (samma som pickup_items max_dist)
const GRIPAVSTAND = 2.2;       // här tar skriptet bollen innan vanilla äter den
const HUND = "dc_hund";
// Det hunden hämtar. Måste stämma med APPORTBARA i tools/make_dogs.py —
// skriptet kan inte läsa entitets-JSON, så strukturtestet jämför listorna.
const APPORTBARA = ["hund:boll", "minecraft:stick", "minecraft:bone"];
const LAGENAMN = ["hund.lage.0", "hund.lage.1", "hund.lage.2"];
const BURET = "hund:buret";    // dynamisk egenskap: vad hunden bär

// TILLSTÅNDET PER HUND behöver bara överleva mellan två varv i loopen. Poängen
// är att INTE trigga samma händelse om och om igen: add/remove av en
// komponentgrupp startar om beteendena, och en hund vars mål nollställs varje
// varv kommer aldrig fram.
const minne = new Map();

function prop(e, namn, fallback) {
  try { const v = e.getProperty(namn); return v === undefined ? fallback : v; }
  catch { return fallback; }
}

function satt(e, namn, varde) {
  try { if (e.getProperty(namn) !== varde) e.setProperty(namn, varde); } catch { }
}

function avstand(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
}

function hundar(dim) {
  try { return dim.getEntities({ families: [HUND] }); } catch { return []; }
}

function agare(hund) {
  // ÄGAREN läses ur tameable-komponenten när det går; annars räknas närmaste
  // spelare inom åtta block som mottagare. Reserven finns för att API-nivåer
  // skiljer sig åt i vad de exponerar, och en hund som aldrig lämnar ifrån sig
  // bollen är sämre än en som i ett hus med två ger den till fel person.
  try {
    const t = hund.getComponent("minecraft:tameable");
    if (t?.tamedToPlayer) return t.tamedToPlayer;
  } catch { }
  try {
    let bast = null, narmast = 8;
    for (const pl of world.getAllPlayers()) {
      if (!pl) continue;
      const d = avstand(pl.location, hund.location);
      if (d < narmast) { bast = pl; narmast = d; }
    }
    return bast;
  } catch { return null; }
}

function sag(pl, nyckel) {
  try { pl.onScreenDisplay.setActionBar({ rawtext: [{ translate: nyckel }] }); } catch { }
}

function foremalNara(dim, plats, radie) {
  try {
    return dim.getEntities({ type: "minecraft:item", location: plats, maxDistance: radie })
      .map(e => {
        let id = null;
        try { id = e.getComponent("minecraft:item")?.itemStack?.typeId; } catch { }
        return APPORTBARA.includes(id) ? { e, id } : null;
      })
      .filter(Boolean);
  } catch { return []; }
}

// Fem tick, inte tjugo: mellan att hunden når fram och att vanilla förstör
// föremålet finns bara ögonblick, och en loop som tittar en gång i sekunden
// missar det ungefär varannan gång.
system.runInterval(() => {
  const d = world.getDimension("overworld");
  const levande = new Set();
  for (const h of hundar(d)) {
    try {
      levande.add(h.id);
      const st = minne.get(h.id) ?? { apport: false, lage: -1, jagar: null };
      minne.set(h.id, st);

      // LÄGESKVITTOT. Växlingen görs av entitetens interact-händelse, som
      // skriptet inte får någon signal om — men egenskapen går att läsa, och
      // en ändring sedan förra varvet betyder att någon just gav kommandot.
      const lage = prop(h, "hund:lage", 0);
      if (st.lage !== -1 && lage !== st.lage) {
        const pl = agare(h);
        if (pl) sag(pl, LAGENAMN[lage] ?? LAGENAMN[0]);
      }
      st.lage = lage;

      if (prop(h, "hund:tam", 0) !== 1) continue;

      if (prop(h, "hund:bar", 0) === 1) {
        // HEMVÄGEN. Apportläget är av, så follow_owner tar hunden hem av sig
        // själv; skriptet väntar bara på att den ska komma fram.
        if (st.apport) { try { h.triggerEvent("hund:apport_av"); } catch { } st.apport = false; }
        const pl = agare(h);
        if (!pl || avstand(pl.location, h.location) > 3) continue;
        let buret = "hund:boll";
        try { buret = h.getDynamicProperty(BURET) ?? buret; } catch { }
        try {
          const inv = pl.getComponent("minecraft:inventory")?.container;
          if (!inv || inv.emptySlotsCount === 0) continue;   // fulla fickor: hunden håller kvar
          inv.addItem(new ItemStack(buret, 1));
        } catch { continue; }
        satt(h, "hund:bar", 0);
        try { h.setDynamicProperty(BURET, undefined); } catch { }
        sag(pl, "hund.apport.klar");
        const L = h.location;
        try {
          d.playSound("mob.wolf.bark", L);
          for (let i = 0; i < 6; i++)
            d.spawnParticle("minecraft:villager_happy",
              { x: L.x + (Math.random() - 0.5), y: L.y + 0.8, z: L.z + (Math.random() - 0.5) });
        } catch { }
        continue;
      }

      // UTVÄGEN. Ligger det något hämtbart i närheten slås apportläget på, och
      // är hunden framme tar skriptet det.
      const nara = foremalNara(d, h.location, RADIE);
      let tog = null;
      for (const { e, id } of nara) {
        if (avstand(e.location, h.location) > GRIPAVSTAND) continue;
        try { e.remove(); } catch { continue; }
        tog = id;
        break;
      }
      // KAPPLÖPNINGEN MOT VANILLA går inte alltid att vinna. Hunden rör sig
      // drygt ett block per varv, och når den fram mitt emellan två varv har
      // vanilla redan förstört bollen: spåret visade hunden stå kvar exakt där
      // bollen låg, utan boll och utan bar. Därför räknas också det HÄR som en
      // lyckad hämtning: det hunden sprang efter försvann medan den var
      // framme. Utan den regeln fungerar apporten bara ungefär varannan gång.
      if (!tog && st.jagar) {
        const kvar = nara.some(x => x.e.id === st.jagar.id);
        if (!kvar && st.jagar.avstand <= 3.5) tog = st.jagar.typ;
      }
      if (tog) {
        satt(h, "hund:bar", 1);
        try { h.setDynamicProperty(BURET, tog); } catch { }
        try { h.triggerEvent("hund:apport_av"); } catch { }
        st.apport = false;
        st.jagar = null;
        try { d.playSound("mob.wolf.bark", h.location); } catch { }
        continue;
      }

      // vad hunden är på väg mot just nu, så nästa varv kan se att det försvann
      let jagat = null;
      for (const { e, id } of nara) {
        const a = avstand(e.location, h.location);
        if (!jagat || a < jagat.avstand) jagat = { id: e.id, typ: id, avstand: a };
      }
      st.jagar = jagat;

      const vill = nara.length > 0;
      if (vill !== st.apport) {
        try { h.triggerEvent(vill ? "hund:apport_pa" : "hund:apport_av"); } catch { }
        st.apport = vill;
      }
    } catch { }
  }
  for (const id of minne.keys()) if (!levande.has(id)) minne.delete(id);
}, 5);

// TESTKROK: /scriptevent hund:test_apport lägger en boll åtta block från en
// tämjd hund. Att den hamnar i munnen läses sedan av testet som en egenskap
// (has_property={hund:bar=1}) — ett kvitto från spelet självt, inte från
// samma skript som utför jobbet.
try {
  system.afterEvents.scriptEventReceive.subscribe(ev => {
    if (ev.id !== "hund:test_apport") return;
    try {
      const d = world.getDimension("overworld");
      const h = hundar(d).find(x => prop(x, "hund:tam", 0) === 1);
      if (!h) { console.warn("[hund] APPORT-TEST FEL: ingen tamd hund"); return; }
      const L = h.location;
      // ÅTTA BLOCK BORT, inte tre: räckvidden är hela poängen med apporten,
      // och en boll inom armlängds avstånd bevisar ingenting om den.
      d.spawnItem(new ItemStack("hund:boll", 1), { x: L.x + 8, y: L.y + 1, z: L.z });
      console.log("[hund] APPORT-TEST: boll lagd 8 block bort");
      // FÖRLOPPET LOGGAS, inte bara utfallet. "Hunden hämtade inte bollen" kan
      // betyda att den stod still, att den gick men inte fram, eller att
      // greppet missade — och de tre kräver helt olika åtgärder.
      const id = h.id;
      let varv = 0;
      const spar = system.runInterval(() => {
        varv++;
        const k = hundar(d).find(x => x.id === id);
        if (!k || varv > 20) { system.clearRun(spar); return; }
        const b = foremalNara(d, k.location, 40)[0];
        const st = minne.get(k.id);
        console.log(`[hund] APPORT-SPAR ${varv}: hund @ ${k.location.x.toFixed(1)},${k.location.z.toFixed(1)}`
          + ` boll ${b ? b.e.location.x.toFixed(1) + "," + b.e.location.z.toFixed(1) : "BORTA"}`
          + ` avstand ${b ? avstand(b.e.location, k.location).toFixed(1) : "-"}`
          + ` apport=${st ? st.apport : "-"} bar=${prop(k, "hund:bar", "-")}`);
      }, 20);
    } catch (e) { console.warn("[hund] APPORT-TEST FEL: " + e); }
  });
} catch { }
