// Prints the Superlift catalogue held in the Mahajan Motors India site as JSON.
// Usage: node scripts/superlift_dump.mjs /abs/path/to/mmi-website/artifacts/mahajan-motors
// Run through scripts/import_superlift.py, which also copies the photos.
const base = process.argv[2];
if (!base) { console.error('pass the path to artifacts/mahajan-motors'); process.exit(1); }
const d = await import(base + '/src/data/superliftData.ts');
const im = await import(base + '/src/data/superliftImages.ts');
const out = [];
for (const car of d.superliftCars) for (const v of car.variants) {
  const img = im.getSuperliftProductImage(v.partNum);
  out.push({
    pn: v.partNum,
    raw: v.rawName,
    car: car.displayName,
    slug: car.slug,
    brand: car.brand,
    app: (img && img.application) || d.getSuperliftApplicationLabel(v),
    pos: d.getSuperliftPosition(v),
    set: d.getSuperliftSetSize(v, car.displayName),
    note: v.note || '',
    img: img ? img.src : '',
    alt: img ? img.alt : '',
    oe: img && img.oe && !img.oe.startsWith('CI ') ? im.formatSuperliftOe(img.oe) : '',
  });
}
console.log(JSON.stringify(out));
