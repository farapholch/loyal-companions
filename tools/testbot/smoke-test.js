// Spelar-röktest: ansluter en RIKTIG klient (bedrock-protocol) till testservern
// och verifierar det servern aldrig kan se från kommandosidan:
//
//   JOIN      klienten tar sig hela vägen till spawn på aktuell MC-version
//   REGISTRY  våra egna föremål finns i item_registry som KLIENTEN får
//   GIVE      egna föremål går att ge en spelare (verklig registrering)
//   ENTITIES  våra entiteter strömmas till klienten med rätt typnamn
//   PROPS     sync_entity_property-paket flödar
//
// PROPS ÄR DEN VIKTIGA HÄR. Halsbandet och bollen i munnen ritas av
// part_visibility, som läser entity properties på KLIENTSIDAN. Att servern
// sätter hund:halsband bevisar ingenting om att klienten får veta det — och
// hela den kedjan var otestad fram till nu.
//
// Vad den INTE testar: att pixlarna ser rätt ut, och interaktioner (servern
// kräver fullt modernt klienthandslag innan den processar interaktionspaket).
//
// Beroendena lånas från kattprojektets testbot; de är samma paket.
const bp = require('/opt/purrfect-testbot/node_modules/bedrock-protocol')
const { spawn } = require('child_process')

const SRV = '/opt/bds/server'
const sleep = (ms) => new Promise(r => setTimeout(r, ms))
const checks = { join: false, registry: [], give: false, entities: new Set(), props: 0 }
let srvlog = ''

const srv = spawn('./bedrock_server', [], { cwd: SRV, env: { ...process.env, LD_LIBRARY_PATH: '.' } })
srv.stdout.on('data', (d) => { srvlog += d.toString() })
const say = (cmd) => srv.stdin.write(cmd + '\n')
const finish = (code) => {
  try { say('stop') } catch {}
  setTimeout(() => { try { srv.kill('SIGKILL') } catch {}; process.exit(code) }, 3000)
}
setTimeout(() => { console.log('FAIL timeout'); finish(1) }, 120000)

async function main () {
  while (!srvlog.includes('Server started')) await sleep(500)
  const client = bp.createClient({ host: '127.0.0.1', port: 19199, username: 'Provhund', offline: true })
  const registry = {}
  client.on('error', (e) => { console.log('FAIL client: ' + e.message); finish(1) })
  client.on('item_registry', (p) => {
    for (const i of p.itemstates || []) registry[i.runtime_id] = i.name
    checks.registry = Object.values(registry).filter(x => x.startsWith('hund:'))
  })
  client.on('add_entity', (p) => { if (p.entity_type.startsWith('hund:')) checks.entities.add(p.entity_type) })
  client.on('sync_entity_property', () => { checks.props++ })
  client.on('inventory_content', (p) => {
    if ((p.input || []).some(s => s && registry[s.network_id] === 'hund:vissla')) checks.give = true
  })

  await new Promise(res => client.on('spawn', res))
  checks.join = true
  say('summon hund:dot 4 102 4')
  say('summon hund:bruno 6 102 4')
  say('give Provhund hund:vissla')
  await sleep(4000)
  // egenskaperna ska SYNKAS till klienten — det är den kedjan halsbandet hänger i
  say('event entity @e[type=hund:dot] hund:on_tame')
  say('event entity @e[type=hund:dot] hund:halsband_5')
  await sleep(4000)

  const rader = [
    ['JOIN', checks.join],
    ['REGISTRY', checks.registry.length >= 2, checks.registry.join(',') || 'inga'],
    ['GIVE', checks.give, 'hund:vissla nådde inventariet'],
    ['ENTITIES', checks.entities.size >= 2, [...checks.entities].join(',')],
    ['PROPS', checks.props >= 1, `${checks.props} property-syncs`],
  ]
  let fel = 0
  for (const [namn, ok, info] of rader) {
    console.log(`${ok ? 'OK  ' : 'FAIL'} ${namn}${info ? ' — ' + info : ''}`)
    if (!ok) fel = 1
  }
  finish(fel)
}
main().catch(e => { console.log('FAIL ' + e.message); finish(1) })
