import { world, system, ItemStack } from "@minecraft/server";
import { RASER } from "./raser.js";

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
// Värdet är också hund:bar, alltså vilken kub renderaren visar i munnen.
const APPORTBARA = { "hund:boll": 1, "minecraft:stick": 2, "minecraft:bone": 3 };
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

// ALLA TRE DIMENSIONERNA. Skriptet arbetade bara i överdimensionen, så en hund
// man tagit med sig till Nether tappade apport, vissla och grävande utan att
// något sa ifrån. Listan byggs en gång; getDimension är billigt men inte
// gratis, och loopen går var femte tick.
const DIMENSIONER = ["overworld", "nether", "the_end"].map(n => {
  try { return world.getDimension(n); } catch { return null; }
}).filter(Boolean);

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
        return id in APPORTBARA ? { e, id } : null;
      })
      .filter(Boolean);
  } catch { return []; }
}

// Fem tick, inte tjugo: mellan att hunden når fram och att vanilla förstör
// föremålet finns bara ögonblick, och en loop som tittar en gång i sekunden
// missar det ungefär varannan gång.
// LOOPENS KOSTNAD mäts av loopen själv. Två klockavläsningar var femte tick är
// försumbart, och utan siffran är "går det långsamt med många hundar?" en
// gissning. Rapporteras av /scriptevent hund:test_last.
let matning = { varv: 0, ms: 0 };

system.runInterval(() => {
  const t0 = Date.now();
  const levande = new Set();
  for (const d of DIMENSIONER) {
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

      // GRÄVPAUSEN ÄR RASENS. En tax är avlad för att gräva och gör det dubbelt
      // så ofta som en bernhardshund. Multiplikatorn kommer ur raser.js, som
      // generatorn skriver ur samma tabell som entiteterna byggs av.
      const gravPaus = GRAVPAUS * (RASER[h.typeId]?.grav ?? 1);
      st.klocka = (st.klocka ?? Math.floor(Math.random() * gravPaus)) + 5;
      if (st.klocka >= gravPaus) {
        st.klocka = 0;
        // bara när någon ser det: en hund som gräver i en tom chunk är bara
        // skräp på marken
        const pl = agare(h);
        if (pl && avstand(pl.location, h.location) < 16) grav(h);
      }

      // VAKTENS VARNING. Hunden morrar när något fientligt närmar sig, men
      // bara i vaktläge och med lång paus — kattpaketets varning sa "your cat
      // bristles" så ofta att den blev tapet, och det var det första Pelle
      // klagade på. Pausen var först 400 tick, alltså tjugo sekunder: exakt
      // samma misstag en gång till, bara i hundform.
      if (lage === 2) {
        st.morr = (st.morr ?? 0) - 5;
        if (st.morr <= 0) {
          let fiende = false;
          try {
            // VARSLET ÄR RASENS. En pomeranian hör och skäller långt före en
            // bernhardshund — det är vad små vakthundar ÄR till för.
            fiende = d.getEntities({ families: ["monster"], location: h.location,
                                     maxDistance: RASER[h.typeId]?.varsel ?? 10 }).length > 0;
          } catch { }
          if (fiende) {
            st.morr = 2400;        // två minuter, se kommentaren ovan
            const pl = agare(h);
            try { d.playSound("mob.wolf.growl", h.location); } catch { }
            if (pl && avstand(pl.location, h.location) < 24) sag(pl, "hund.vakt");
          }
        }
      }

      if (prop(h, "hund:bar", 0) !== 0) {
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
        satt(h, "hund:bar", APPORTBARA[tog] ?? 1);
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

      // STANNA BETYDER STANNA. Apportläget lades på oavsett kommando, och
      // pickup_items flyttar hunden — en hund man beordrat att stanna gick
      // alltså sin väg så fort någon tappat en pinne inom sexton block.
      const vill = nara.length > 0 && lage !== 1;
      if (vill !== st.apport) {
        try { h.triggerEvent(vill ? "hund:apport_pa" : "hund:apport_av"); } catch { }
        st.apport = vill;
      }
    } catch { }
  }
  }
  for (const id of minne.keys()) if (!levande.has(id)) minne.delete(id);
  matning.varv++;
  matning.ms += Date.now() - t0;
}, 5);

// ---------------------------------------------------------------------------
// VISSLAN. Ett tryck och alla dina hundar kommer — och går tillbaka till att
// följa. Att leta reda på en hund som blivit kvar tre dalar bort är inte
// roligt, och ett glömt stannakommando är den vanligaste vägen dit.
const VISSELRADIE = 96;

function vissla(plats, pl, dim) {
  // SAMMA DIMENSION SOM DEN SOM BLÅSER. En vissla som teleporterar hundar
  // mellan dimensioner vore inte en vissla, det vore en portal.
  const d = dim ?? DIMENSIONER[0];
  let n = 0;
  for (const h of hundar(d)) {
    try {
      if (prop(h, "hund:tam", 0) !== 1) continue;
      if (avstand(h.location, plats) > VISSELRADIE) continue;
      if (pl) {
        const a = agare(h);
        if (a && a.id !== pl.id) continue;
      }
      // TILLBAKA TILL FÖLJA. Kommer hunden springande och sedan står kvar för
      // att den är i stannaläge är visslan bara en teleport, inte ett kommando.
      if (prop(h, "hund:lage", 0) !== 0) {
        try { h.triggerEvent("hund:till_foljer"); } catch { }
      }
      const v = 1.6 + (n % 4) * 0.7, vinkel = (n % 8) * Math.PI / 4;
      try {
        h.teleport({ x: plats.x + Math.cos(vinkel) * v, y: plats.y,
                     z: plats.z + Math.sin(vinkel) * v });
      } catch (fel) { console.warn("[hund] VISSLA: teleport misslyckades " + fel); continue; }
      try {
        d.playSound("mob.wolf.bark", h.location);
        for (let i = 0; i < 5; i++)
          d.spawnParticle("minecraft:villager_happy",
            { x: h.location.x, y: h.location.y + 0.8 + i * 0.1, z: h.location.z });
      } catch { }
      n++;
    } catch (fel) { console.warn("[hund] VISSLA: " + fel); }
  }
  return n;
}

try {
  world.afterEvents.itemUse.subscribe(ev => {
    try {
      if (ev.itemStack?.typeId !== "hund:vissla") return;
      const pl = ev.source;
      const n = vissla(pl.location, pl, pl.dimension);
      sag(pl, n ? "hund.vissla.kom" : "hund.vissla.ingen");
      try { pl.dimension.playSound("random.orb", pl.location); } catch { }
    } catch { }
  });
} catch { }

// ---------------------------------------------------------------------------
// GRÄVANDET. En hund som bara går bredvid är en tapet. Med jämna mellanrum
// gräver den upp något ur marken — mest skräp, ibland något värt att ha.
// AVSVALNINGEN ÄR LÅNG med flit: hittar hunden guld var tionde sekund är den
// inte en hund längre, den är en gruva.
const GRAVPAUS = 5400;                        // 4,5 minuter i tick
const SKATT = [
  ["minecraft:bone", 40], ["minecraft:stick", 40], ["minecraft:string", 30],
  ["minecraft:wheat_seeds", 25], ["minecraft:leather", 15], ["minecraft:rotten_flesh", 15],
  ["minecraft:iron_nugget", 10], ["minecraft:flint", 10], ["minecraft:gold_nugget", 5],
  ["minecraft:lapis_lazuli", 3], ["minecraft:emerald", 1],
];
const SKATTVIKT = SKATT.reduce((a, b) => a + b[1], 0);

function grav(h) {
  const d = h.dimension;
  let r = Math.floor(Math.random() * SKATTVIKT);
  let vald = SKATT[0][0];
  for (const [id, vikt] of SKATT) {
    if (r < vikt) { vald = id; break; }
    r -= vikt;
  }
  const L = h.location;
  try {
    d.spawnItem(new ItemStack(vald, 1), { x: L.x, y: L.y + 0.4, z: L.z });
    d.playSound("dig.gravel", L);
    for (let i = 0; i < 8; i++)
      d.spawnParticle("minecraft:crop_growth_emitter",
        { x: L.x + (Math.random() - 0.5), y: L.y + 0.2, z: L.z + (Math.random() - 0.5) });
  } catch { return null; }
  const pl = agare(h);
  if (pl) sag(pl, "hund.grav");
  return { typ: vald, plats: { x: L.x, y: L.y, z: L.z } };
}

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

// TESTKROKAR för visslan och grävandet. Båda kräver egentligen en spelare —
// visslan utlöses av att någon använder ett föremål, grävandet av att någon är
// i närheten — och en simulerad spelare är osynlig för ett annat pakets skript.
// Krokarna kör därför samma funktioner med en plats i stället för en spelare.
try {
  system.afterEvents.scriptEventReceive.subscribe(ev => {
    const d = world.getDimension("overworld");
    if (ev.id === "hund:test_vissla") {
      // hunden flyttas långt bort och ska komma tillbaka av visslan ensam
      const h = hundar(d).find(x => prop(x, "hund:tam", 0) === 1);
      if (!h) { console.warn("[hund] VISSEL-TEST FEL: ingen tamd hund"); return; }
      const mal = { x: 10, y: 21, z: 10 };
      // TRETTIO BLOCK, inte fyrtio: bortom testvärldens korridor står hunden i
      // berg, och en hund som kvävts kan ingen vissla hämta hem.
      try { h.teleport({ x: mal.x + 30, y: mal.y, z: mal.z }); } catch (e) {
        console.warn("[hund] VISSEL-TEST: teleport ut misslyckades " + e);
      }
      system.runTimeout(() => {
        try {
          const kvar = hundar(d).filter(x => prop(x, "hund:tam", 0) === 1);
          console.log(`[hund] VISSEL-TEST: ${kvar.length} tamda hundar, avstand `
            + kvar.map(x => avstand(x.location, mal).toFixed(1)).join("/"));
          const n = vissla(mal, null);
          const k = hundar(d).find(x => prop(x, "hund:tam", 0) === 1);
          const a = k ? avstand(k.location, mal) : 999;
          if (n && a < 5) console.log(`[hund] VISSEL-TEST OK: ${n} hund(ar), avstand ${a.toFixed(1)}`);
          else console.warn(`[hund] VISSEL-TEST FEL: ${n} hund(ar), avstand ${a.toFixed(1)}`);
        } catch (e) { console.warn("[hund] VISSEL-TEST FEL: " + e); }
      }, 40);
    }
    if (ev.id === "hund:test_last") {
      const n = hundar(d).length;
      const snitt = matning.varv ? matning.ms / matning.varv : 0;
      console.log(`[hund] LAST-TEST: ${n} hundar, ${matning.varv} varv, `
        + `${snitt.toFixed(2)} ms per varv (budget 50 ms/tick)`);
      matning = { varv: 0, ms: 0 };
    }
    if (ev.id === "hund:test_satt") {
      // sätter allt som ska överleva en omstart
      const h = hundar(d).find(x => x.nameTag === "Uthall");
      if (!h) { console.warn("[hund] SPARA-TEST FEL: hittar inte Uthall"); return; }
      try {
        h.setProperty("hund:bar", 2);
        h.setDynamicProperty(BURET, "minecraft:stick");
        console.log("[hund] SPARA-TEST: bar=2 och buret=minecraft:stick satta");
      } catch (e2) { console.warn("[hund] SPARA-TEST FEL: " + e2); }
    }
    if (ev.id === "hund:test_las") {
      const h = hundar(d).find(x => x.nameTag === "Uthall");
      if (!h) { console.warn("[hund] LAS-TEST FEL: Uthall overlevde inte omstarten"); return; }
      let buret = null;
      try { buret = h.getDynamicProperty(BURET); } catch { }
      const rad = `tam=${prop(h, "hund:tam", "-")} lage=${prop(h, "hund:lage", "-")} `
        + `halsband=${prop(h, "hund:halsband", "-")} bar=${prop(h, "hund:bar", "-")} buret=${buret}`;
      const helt = prop(h, "hund:tam", 0) === 1 && prop(h, "hund:lage", -1) === 1
        && prop(h, "hund:halsband", 0) === 5 && prop(h, "hund:bar", 0) === 2
        && buret === "minecraft:stick";
      if (helt) console.log(`[hund] LAS-TEST OK: ${rad}`);
      else console.warn(`[hund] LAS-TEST FEL: ${rad}`);
    }
    if (ev.id === "hund:test_stanna") {
      // STANNA MOT FRESTELSE. En hund i stannaläge ska INTE gå efter en boll.
      // Buggen var att apportläget slogs på oavsett kommando, och pickup_items
      // flyttar hunden — stannakommandot gällde tills någon tappade en pinne.
      const h = hundar(d).find(x => prop(x, "hund:lage", -1) === 1);
      if (!h) { console.warn("[hund] STANNA-TEST FEL: ingen hund i stannaläge"); return; }
      const start = { x: h.location.x, y: h.location.y, z: h.location.z };
      const id = h.id;
      d.spawnItem(new ItemStack("hund:boll", 1), { x: start.x + 8, y: start.y + 1, z: start.z });
      system.runTimeout(() => {
        try {
          const k = hundar(d).find(x => x.id === id);
          if (!k) { console.warn("[hund] STANNA-TEST FEL: hunden forsvann"); return; }
          const flytt = avstand(k.location, start);
          const bollkvar = d.getEntities({ type: "minecraft:item", location: start,
                                           maxDistance: 20 }).length;
          if (flytt < 3 && bollkvar)
            console.log(`[hund] STANNA-TEST OK: rorde sig ${flytt.toFixed(1)} block, bollen kvar`);
          else
            console.warn(`[hund] STANNA-TEST FEL: rorde sig ${flytt.toFixed(1)} block, `
              + `${bollkvar} bollar kvar`);
        } catch (e2) { console.warn("[hund] STANNA-TEST FEL: " + e2); }
      }, 200);
    }
    if (ev.id === "hund:test_foremal") {
      // ÄR VÅRA EGNA FÖREMÅL REGISTRERADE? Ett föremål som inte laddat gör att
      // new ItemStack kastar. Bollen bevisas redan av apporttestet, men
      // visslan fanns aldrig i någon körning — och ett recept som ger ett
      // föremål spelet inte känner till syns först när någon försöker
      // tillverka det.
      const vill = ["hund:boll", "hund:vissla"];
      let n = 0;
      for (const id of vill) {
        try {
          const e = d.spawnItem(new ItemStack(id, 1), { x: 10, y: 22, z: 10 });
          if (e) { n++; e.remove(); }
        } catch (fel) { console.warn(`[hund] FOREMAL-TEST: ${id} gick inte att skapa: ${fel}`); }
      }
      console.log(`[hund] FOREMAL-TEST ${n === vill.length ? "OK" : "FEL"}: ${n}/${vill.length}`);
    }
    if (ev.id === "hund:test_grav") {
      const h = hundar(d).find(x => prop(x, "hund:tam", 0) === 1);
      if (!h) { console.warn("[hund] GRAV-TEST FEL: ingen tamd hund"); return; }
      const fynd = grav(h);
      if (!fynd) { console.warn("[hund] GRAV-TEST FEL: inget grävdes upp"); return; }
      system.runTimeout(() => {
        try {
          // SÖK VID GROPEN, inte vid hunden. Hunden hinner gå fyra block på en
          // sekund, och då låg fyndet utanför sökradien fast allt fungerat.
          const kvar = d.getEntities({ type: "minecraft:item", location: fynd.plats,
                                       maxDistance: 6 }).length;
          // HUNDEN HÄMTAR OFTA SITT EGET FYND. Ben och pinnar står på
          // apportlistan, så den plockar upp dem inom en sekund — testet
          // rapporterade "fyndet finns inte" när det som hänt var att hunden
          // gjort precis det den ska.
          const k = hundar(d).find(x => x.id === h.id);
          const bar = k ? prop(k, "hund:bar", 0) : 0;
          if (kvar || bar) console.log(`[hund] GRAV-TEST OK: ${fynd.typ}`
            + (kvar ? " ligger pa marken" : " hamtades direkt av hunden"));
          else console.warn("[hund] GRAV-TEST FEL: fyndet finns inte");
        } catch (e) { console.warn("[hund] GRAV-TEST FEL: " + e); }
      }, 20);
    }
  });
} catch { }
