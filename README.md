# natuurspeld.nl

Het archief van NatuurSpeld: verkeerde natuurinformatie in het nieuws, op
informatieborden, in boeken en op social media. Statisch gehost op GitHub Pages,
geserveerd vanaf de root van `main`.

Tot 22 augustus 2026 stuurde dit domein alleen door naar Instagram. De inhoud van
het archief is geoogst uit de Instagram-posts van
[@natuurspeld](https://www.instagram.com/natuurspeld/).

## Bouwen

```
python3 build.py
```

Leest `content/posts.json` en `content/stijl.css` en schrijft `index.html`,
`post/<slug>.html`, `stijl.css`, `sitemap.xml`, `robots.txt` en `404.html` naar
de root. De beelden in `beeld/` worden niet aangeraakt.

## Een post toevoegen

Voeg een object toe aan `content/posts.json` en zet de beelden in `beeld/`.

| veld | wat |
|------|-----|
| `slug` | url-naam, ook de basis van de bestandsnamen van de beelden |
| `code` | de Instagram-shortcode, voor de link naar de originele post |
| `datum` | `JJJJ-MM-DD` |
| `titel` | de vorm "X, geen Y" waar dat kan; daar wordt op gezocht |
| `orgs` | lijst met aangesproken organisaties, leeg bij een anonieme inzending |
| `fout` | wat er op de foto staat |
| `goed` | waar de tekst over ging |
| `groep` | `vogels`, `zoogdieren`, `insecten`, `planten` of `overig` |
| `caption` | de posttekst; hashtags worden er automatisch uitgehaald |
| `beelden` | lijst met `groot`, `klein`, `w`, `h` |
| `rectificatie` | optioneel, zie hieronder |

Beelden worden opgeslagen als `<slug>-<n>.jpg` (maximaal 1100 px breed of hoog)
en `<slug>-<n>-klein.jpg` (maximaal 560 px).

## Rectificaties

Past de aangesproken partij de fout aan, dan komt dat als `rectificatie` boven de
beelden te staan. De post blijft staan, met de correctie erbij.

## DNS

Apex A/AAAA staan op de GitHub Pages-adressen, `www` is een CNAME naar
`wvdham.github.io`. Beheerd bij Mijndomein.
