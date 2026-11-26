// Builds the portal's ZOHO_FIELD_MAP file from the gateway's maps.json (ids and names only, no secrets), so the payload the portal builds is one
// the gateway accepts (spec 18 F10: shared ids). Format = order-portal-s1 test/fixtures/zoho-field-map.json (read by server/services/zoho-payload.js:9-20,54-62).
// Usage: node make-portal-field-map.mjs            (reads /root/demo/order-portal-gateway/tools/demo-gateway/data/maps.json, writes /root/demo/order-portal/data/field-map.json)
// Prepared by Abdul Hadhee | IT Executive
import fs from 'node:fs';

const MAPS = '/root/demo/order-portal-gateway/tools/demo-gateway/data/maps.json';
const OUT = '/root/demo/order-portal/data/field-map.json';
const PLACEHOLDER = '4892105000000168085';          // the SH customer / placeholder contact (gateway default PLACEHOLDER_CONTACT_ID)
const WAREHOUSE = '7000000000000700001';            // stand-in: the gateway does not read warehouse_id (NEEDS-VALUE for v0.5 live writes)
// Portal division code -> Division tag option NAME in maps.json, and the text the Manufacturing Division field carries.
// Tag and option names as recorded on real SPS orders (pd-zoho-study details.json: line tag x header division, 28 Oct). Owners (28 Oct):
// Shihar MACPRO; Ishan PACKPRO + PSU; Ranga PCU, PCLU, PPU, CWU, MOBA, FPP, CPU, DPU; Ishan also RWU; Mubeena SHPS. A name missing from maps.json stops this script.
const DIVISIONS = {
  MACPRO: { tag: 'OPD - MacPro Unit', option: 'Offset Printing Division (OPD)' },
  PACKPRO: { tag: 'OPD - PackPro Unit', option: 'Offset Printing Division (OPD)' },
  PSU: { tag: 'Paper Straw Unit', option: 'Paper Straw Unit (PSU)' },
  PCU: { tag: 'MOBA Unit', option: 'Paper Cup Unit (PCU)' },
  PCLU: { tag: 'MOBA Unit', option: 'Paper Cup Lid Unit' },
  PPU: { tag: 'MOBA Unit', option: 'Paper Plate Unit' },
  CWU: { tag: 'MOBA Unit', option: 'Cake Wrapper Unit' },
  MOBA: { tag: 'MOBA Punching Unit', option: 'MOBA Punching Unit' },
  FPP: { tag: 'Food Product Processing Unit', option: 'Food Product Processing (FPP)' },
  SHPS: { tag: 'Screen Printing Unit', option: 'Screen Printing Division (SHPS)' },
  CPU: { tag: 'Customized Packing Unit', option: 'Customized Packing Unit (CPU)' },
  DPU: { tag: 'Digital Printing Unit', option: 'Digital Printing Unit (DPU)' },
  // RWU (Ishan) is left out: no recorded SPS line carries a Rewinding Division tag option, so maps.json has none and a portal approval
  // for an RWU line would stop with "division RWU is not in the field map". Add it once the owner reads the option name in Zoho.
};

const maps = JSON.parse(fs.readFileSync(MAPS, 'utf8'));
const [tagId, tag] = Object.entries(maps.tags).find(([, t]) => t.name === 'Division') ?? [];
if (!tagId) throw new Error('maps.json has no "Division" tag');
const optionId = (name) => Object.entries(tag.options).find(([, n]) => n === name)?.[0];
const custom = {};
for (const [id, f] of Object.entries(maps.custom_fields)) custom[f.api_name] = id;
for (const need of ['cf_order_received_from', 'cf_material_to_be_used', 'cf_additional_other_material_t', 'cf_sh_sales_order_ref', 'cf_job_no', 'cf_order_type',
  'cf_manufacturing_division', 'cf_job_nature', 'cf_artwork_availablility', 'cf_dye_cutter_availablity', 'cf_screen_plate_availability_2', 'cf_portal_ref']) {
  if (!custom[need]) throw new Error(`maps.json has no custom field ${need}`);
}
const divisions = {};
for (const [code, d] of Object.entries(DIVISIONS)) {
  const id = optionId(d.tag);
  if (!id) throw new Error(`maps.json has no Division option named "${d.tag}"`);
  divisions[code] = { tag_option_id: id, option: d.option };
}
const map = { customer_id: PLACEHOLDER, placeholder_contact_id: PLACEHOLDER, warehouse_id: WAREHOUSE, division_tag_id: tagId, custom_fields: custom, divisions };
fs.mkdirSync(OUT.replace(/\/[^/]+$/, ''), { recursive: true, mode: 0o700 });
fs.writeFileSync(OUT, `${JSON.stringify(map, null, 2)}\n`, { mode: 0o600 });
console.log(`wrote ${OUT}: ${Object.keys(custom).length} custom fields, divisions ${Object.keys(divisions).join(', ')}, tag ${tag.name}`);
