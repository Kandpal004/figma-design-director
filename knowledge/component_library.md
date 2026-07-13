# COMPONENT LIBRARY — proven, working patterns (reuse; don't rebuild)

Copy these into any section. They already pass the slop gate and encode the house style.
Read `knowledge/design_dna.md` for the rules; this file is the code.

## Base tokens + fonts (put once in <head>)
```html
<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap" rel="stylesheet">
<style>:root{
  --brand:#a10047;--brand-tint:#fbeef3;--brand-dark:#800038;
  --ink:#1c1b1d;--ink-2:#4c505b;--muted:#8a8f99;--line:#ececee;--line-2:#e2e2e6;
  --field:#f5f5f7;--ok:#1f7a4d;--teal:#0d7a6f;--dark:#201c1d;--paper:#fff;
  --f:"Hanken Grotesk",system-ui,sans-serif;--logo:"Playfair Display",Georgia,serif;}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--f);color:var(--ink);font-weight:400}   /* min 400 for readability */</style>
```
Gallery "More Colours" overlays the product image, first fold (desktop):
```css
.stage{position:relative}
.more-colours{position:absolute;left:16px;bottom:16px;display:flex;align-items:center;gap:8px;background:rgba(255,255,255,.95);border:1px solid var(--line-2);border-radius:24px;padding:6px 8px 6px 14px;font-size:12.5px;font-weight:600;cursor:pointer}
.more-colours .sw{display:flex} .more-colours .sw i{width:18px;height:18px;border-radius:50%;border:2px solid #fff;margin-left:-6px;box-shadow:0 0 0 1px var(--line-2)}
```

## Premium header — two variants
- **Editorial** (headlinehq style): utility strip (Book a Styling Call · shipping ticker ·
  region) → centred `ANDAAZ`/`Fashion` Playfair wordmark with `Menu/Search` (left) +
  `Account/Wishlist/Bag` (right) as icon+letter-spaced-label → nav (letter-spaced uppercase,
  accent hover-underline). WHITE bg only.
- **Retail** (andaazfashion.com style): dark shipping bar → logo-left + big search + `Need
  Help?` + sharp account/wishlist/bag icons + India flag → full category nav with a rani
  "Buy any 2" promo pill + "New" badge.
Icons: `stroke-width:1.5-1.6; stroke-linecap:round; stroke-linejoin:round`. See
`output/*/sections/header.html` and `page-desktop.html` for full markup.

## Working stitching option + size + live price (the key interactive PDP piece)
Mirrors Andaaz Magento `pdp.js`. Radios drive a `recalc()`; "Stitched" reveals size+height.
```html
<div class="chips" id="stitch">
  <label class="chip on"><input type="radio" name="stitch" data-price="0" data-label="Unstitched" data-desc="Fabric only — no stitching included. Perfect for custom tailoring at your own discretion." checked>Unstitched</label>
  <label class="chip"><input type="radio" name="stitch" data-price="15" data-label="Stitched" data-desc="">Stitched <small>+$15</small></label>
  <label class="chip"><input type="radio" name="stitch" data-price="15" data-label="Custom Stitched" data-desc="Get a made-to-measure outfit — customize every detail for your perfect fit.">Custom Stitched <small>+$15</small></label>
</div>
<p class="note" id="stitch-desc"></p>
<section id="sizesec" hidden>
  <div class="lbl">Size: <strong id="size-label">32</strong> <span class="hsub">Prices may vary by plus size</span></div>
  <div class="chips sizegrid" id="sizegrid"></div>
</section>
<section id="heightsec" hidden>
  <label>Select Your Height <span class="hsub">(Including heels)</span> *</label>
  <select id="hsel"><option value="">Please Select</option><option>4'10"</option><option>5'0"</option><option>5'2"</option><option>5'4"</option><option>5'6"</option><option>5'8"</option><option>6'0"</option></select>
</section>
```
```js
// REAL Andaaz size options (label, +$ surcharge). Use these unless extraction gives others.
const SIZES=[["32",0],["33",0],["34",0],["35",0],["36",0],["37",0],["38",0],["40",0],["42",0],["44",5],["46",8],["48",10],["50",12],["52",15],["54",18],["56",20],["58",22],["60",25],["63",30],["66",35],["69",40]];
const $=s=>document.querySelector(s), grid=$('#sizegrid');
grid.innerHTML=SIZES.map((s,i)=>`<button type="button" class="chip${i?'':' on'}" data-price="${s[1]}" data-label="${s[0]}">${s[0]}${s[1]?`<small>+$${s[1]}.00</small>`:''}</button>`).join('');
const fEl=$('#apdp-final'),rEl=$('#apdp-regular'),oEl=$('#apdp-off'),bF=+fEl.dataset.base,bR=+rEl.dataset.base;
const money=n=>'$'+(Math.round(n*100)/100).toFixed(2);
function recalc(){let x=0;const st=$('#stitch input:checked');if(st)x+=+st.dataset.price;
  if(!$('#sizesec').hidden){const sp=grid.querySelector('.chip.on');if(sp)x+=+sp.dataset.price;}
  document.querySelectorAll('.arow.on').forEach(a=>x+=+a.dataset.price);
  const f=bF+x,r=bR+x;fEl.textContent=money(f);rEl.textContent=money(r);oEl.textContent=Math.round((r-f)/r*100)+'% Off';
  const sp=$('#sb-price'),sw=$('#sb-was');if(sp)sp.textContent=money(f);if(sw)sw.textContent=money(r);}
function applyStitch(){const st=$('#stitch input:checked'),isS=st.dataset.label==='Stitched';
  $('#sizesec').hidden=!isS;$('#heightsec').hidden=!isS;
  $('#stitch-desc').textContent=st.dataset.desc||'';$('#stitch-desc').style.display=st.dataset.desc?'block':'none';
  document.querySelectorAll('#stitch .chip').forEach(l=>l.classList.toggle('on',l.querySelector('input').checked));recalc();}
document.querySelectorAll('#stitch input').forEach(r=>r.addEventListener('change',applyStitch));
grid.querySelectorAll('.chip').forEach(p=>p.addEventListener('click',()=>{grid.querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));p.classList.add('on');$('#size-label').textContent=p.dataset.label;recalc();}));
document.querySelectorAll('.arow').forEach(r=>r.addEventListener('click',()=>{r.classList.toggle('on');recalc();}));
applyStitch();
```
Active chip style: `.chip.on{background:var(--ink);color:#fff;border-color:var(--ink)}`.
Price element: `<span id="apdp-final" data-base="149">$149.00</span>` + `#apdp-regular data-base` + `#apdp-off`.

**ALWAYS include the "Customize your outfit" help button** (real Andaaz shows it under the
stitching options in ALL states). Full-width outlined premium button, pencil icon, opens a
help popup. No long dash in the label:
```html
<button class="custom-help" data-popup data-title="Customize your outfit" data-body="Our stylists help you personalise measurements, colours and add-ons.">
  <svg viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"/></svg>
  Customize your outfit, get help here.</button>
```
```css
.custom-help{display:flex;align-items:center;justify-content:center;gap:10px;width:100%;margin-top:16px;padding:15px 18px;background:#fff;border:1px solid var(--line-2);border-radius:6px;font-weight:600;font-size:13.5px}
.custom-help svg{width:17px;height:17px;stroke:var(--brand);stroke-width:1.7;fill:none}
.custom-help:hover{border-color:var(--brand);background:var(--brand-tint);color:var(--brand-dark)}
```

## Always-sticky premium add-to-cart bar
```html
<div class="stickybar"><div class="in">
  <span class="sb-thumb"><img src="../images/img-0.jpg" alt=""></span>
  <div class="sb-info"><div class="sb-name">Product name…</div>
    <div class="sb-price"><b id="sb-price">$149.00</b> <s id="sb-was">$199.00</s></div></div>
  <div class="sb-cta"><button class="add" id="sb-add">Add to Cart</button><button class="buy">Buy It Now</button></div>
</div></div>
```
```css
.stickybar{position:fixed;left:0;right:0;bottom:0;z-index:80;background:rgba(255,255,255,.96);backdrop-filter:blur(10px);border-top:1px solid var(--line-2);box-shadow:0 -6px 24px -18px rgba(0,0,0,.3)}
.stickybar .in{max-width:1440px;margin:0 auto;padding:11px 40px;display:flex;align-items:center;gap:20px}
.sb-cta .add{background:var(--brand);color:#fff}.sb-cta .buy{background:var(--ink);color:#fff}
```
Add `body{padding-bottom:76px}` so it doesn't cover content.

## Offers pill (inline, opens popup — NOT a big dashed box)
```html
<button class="offersbtn" data-popup data-title="Offers" data-body="…">🏷 4 Offers →</button>
```
`.offersbtn{background:var(--brand);color:#fff;border-radius:22px;padding:9px 15px;font-weight:600}`

## Trust row / spec table / accordions
Trust: 2–3 col grid, rani line-icons + short labels (100% Purchase Protection · Delivered Duty
Paid · 15 Days Easy Returns · Assured Quality · Free Shipping). Spec: 2-col key/value with
hairline rows. Accordions: Style & Fit Tips · Shipping & Returns · FAQs (+ toggle).

## Real Andaaz PDP data (grounding for the sample product)
Title: "Pink Palazzo Set With Zari Embroidered A-Line Kurta And Dupatta" · $149 (was $199, 25%)
· SKU SG222133 · Ships by 02 Jun · PayPal Pay-in-4 $37.25 · rating 4.3/5 (6 reviews) ·
Stitching Unstitched/Stitched(+$15)/Custom(+$15) · Add-ons: Matching Dupatta $45(+$25),
Potli $35(+$18), Jewellery $80(+$40), Blouse $30(+$15) · Fabric Art Silk, Zari, A-Line,
Round Neck, 3/4 Sleeves, Palazzo, Dupatta Included, Festive & Wedding, Dry Clean Only.
Real images: `output/andaaz-bvffgzb8fdewg8cq-z03-azurefd-net/images/img-0..5.jpg`.
