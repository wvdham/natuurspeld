#!/usr/bin/env python3
"""Bouwt natuurspeld.nl uit content/posts.json.

Bron:   content/posts.json  (geoogst uit de Instagram-posts) + content/stijl.css
Uitvoer: index.html, post/<slug>.html, stijl.css, sitemap.xml, robots.txt
GitHub Pages serveert deze repo vanaf de root.
"""
import html
import json
import re
import shutil
from datetime import date
from pathlib import Path

WORTEL = Path(__file__).resolve().parent
CONTENT = WORTEL / "content"
SITE = "https://natuurspeld.nl"
INSTA = "https://www.instagram.com/natuurspeld/"

GROEPEN = [
    ("alles", "Alles"),
    ("vogels", "Vogels"),
    ("zoogdieren", "Zoogdieren"),
    ("insecten", "Insecten"),
    ("planten", "Planten"),
    ("overig", "Overig"),
]

MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
           "augustus", "september", "oktober", "november", "december"]


def datum_nl(iso):
    j, m, d = (int(x) for x in iso.split("-"))
    return f"{d} {MAANDEN[m - 1]} {j}"


def tekst_naar_html(caption):
    """Caption opsplitsen in alinea's, hashtagblok eruit, @-vermeldingen markeren."""
    tags = re.findall(r"#(\w+)", caption)
    kaal = re.sub(r"#\w+", "", caption)
    alineas = []
    for stuk in re.split(r"\n\s*\n|\n", kaal):
        stuk = stuk.strip()
        if not stuk or stuk in {"-", "- -", "- - - -"}:
            continue
        stuk = re.sub(r"(?:\s*-\s*){2,}$", "", stuk).strip()
        if not stuk:
            continue
        veilig = html.escape(stuk)
        veilig = re.sub(r"@([\w.]+)", r'<span class="mention">@\1</span>', veilig)
        alineas.append(f"<p>{veilig}</p>")
    return "\n      ".join(alineas), tags


def samenvatting(caption, lengte=155):
    plat = " ".join(re.sub(r"#\w+", "", caption).split())
    if len(plat) <= lengte:
        return plat
    return plat[:lengte].rsplit(" ", 1)[0] + "..."


def pagina(titel, beschrijving, inhoud, pad_naar_wortel="", og_beeld=None, canoniek=""):
    og = f'\n<meta property="og:image" content="{SITE}/beeld/{og_beeld}">' if og_beeld else ""
    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titel)}</title>
<meta name="description" content="{html.escape(beschrijving)}">
<link rel="canonical" href="{SITE}{canoniek}">
<meta property="og:site_name" content="NatuurSpeld">
<meta property="og:title" content="{html.escape(titel)}">
<meta property="og:description" content="{html.escape(beschrijving)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{SITE}{canoniek}">{og}
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="{pad_naar_wortel}stijl.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><text y='26' font-size='26'>&#128269;</text></svg>">
</head>
<body>
{inhoud}
</body>
</html>
"""


VOET = f"""<footer>
  <div class="wrap">
    <h2>Iets gezien?</h2>
    <p>Kom je verkeerde natuurinformatie tegen in het nieuws, op een informatiebord, in een
       boek of op social media? Stuur de foto of de schermafdruk op, dan zoeken we het uit.
       Inzenders blijven standaard anoniem.</p>
    <div class="links">
      <a href="{INSTA}">Instagram</a>
      <a href="https://www.facebook.com/natuurspeld">Facebook</a>
      <a href="https://www.linkedin.com/company/natuurspeld">LinkedIn</a>
    </div>
  </div>
</footer>"""


def bouw_index(posts):
    per_jaar = {}
    for p in posts:
        per_jaar.setdefault(p["datum"][:4], []).append(p)

    blokken = []
    for jaar in sorted(per_jaar, reverse=True):
        kaarten = []
        for p in per_jaar[jaar]:
            beeld = p["beelden"][0] if p["beelden"] else None
            thumb = (f'<img src="beeld/{beeld["klein"]}" alt="" loading="lazy" width="560" height="420">'
                     if beeld else "")
            orgs = ", ".join(p["orgs"]) if p["orgs"] else "Ingezonden"
            zoek = html.escape(" ".join([p["titel"], orgs, p["fout"], p["goed"], p["groep"]]).lower())
            kaarten.append(f"""        <a class="kaart" href="post/{p['slug']}.html" data-groep="{p['groep']}" data-zoek="{zoek}">
          <div class="beeld">{thumb}</div>
          <h2>{html.escape(p['titel'])}</h2>
          <div class="onder">{html.escape(orgs)} &middot; {datum_nl(p['datum'])}</div>
        </a>""")
        blokken.append(f"""      <section class="jaargroep" data-jaar="{jaar}">
        <h2 class="jaar">{jaar}</h2>
        <div class="raster">
{chr(10).join(kaarten)}
        </div>
      </section>""")

    chips = "\n        ".join(
        f'<button class="chip" data-groep="{k}" aria-pressed="{"true" if k == "alles" else "false"}">{v}</button>'
        for k, v in GROEPEN)

    inhoud = f"""<header class="kop">
  <div class="wrap">
    <h1 class="merk">NatuurSpeld</h1>
    <p>Verkeerde natuurinformatie in het nieuws, op informatieborden, in boeken en op social
       media. Wat er staat, wat het werkelijk is, en waar je het verschil aan ziet.
       <span class="telling">{len(posts)} gevallen sinds 2020.</span></p>
  </div>
</header>

<div class="filter">
  <div class="wrap">
    <div class="rij">
      <input id="zoek" type="search" placeholder="Zoek op soort of organisatie" aria-label="Zoek op soort of organisatie">
        {chips}
    </div>
  </div>
</div>

<main class="wrap">
{chr(10).join(blokken)}
  <p class="leeg" id="leeg">Niets gevonden.</p>
</main>

{VOET}

<script>
(function () {{
  var zoek = document.getElementById('zoek');
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip'));
  var kaarten = Array.prototype.slice.call(document.querySelectorAll('.kaart'));
  var groepen = Array.prototype.slice.call(document.querySelectorAll('.jaargroep'));
  var leeg = document.getElementById('leeg');
  var groep = 'alles';

  function ververs() {{
    var term = zoek.value.trim().toLowerCase();
    var zichtbaar = 0;
    kaarten.forEach(function (k) {{
      var ok = (groep === 'alles' || k.dataset.groep === groep) &&
               (term === '' || k.dataset.zoek.indexOf(term) !== -1);
      k.hidden = !ok;
      if (ok) zichtbaar++;
    }});
    groepen.forEach(function (g) {{
      g.hidden = !g.querySelector('.kaart:not([hidden])');
    }});
    leeg.style.display = zichtbaar ? 'none' : 'block';
  }}

  zoek.addEventListener('input', ververs);
  chips.forEach(function (c) {{
    c.addEventListener('click', function () {{
      groep = c.dataset.groep;
      chips.forEach(function (x) {{ x.setAttribute('aria-pressed', String(x === c)); }});
      ververs();
    }});
  }});
}})();
</script>"""

    return pagina(
        "NatuurSpeld, verkeerde natuurinformatie onder de loep",
        "Archief van verkeerde natuurinformatie in nieuws, boeken en op informatieborden. "
        f"{len(posts)} gevallen, met per geval wat er stond en wat het werkelijk is.",
        inhoud, "", posts[0]["beelden"][0]["groot"] if posts[0]["beelden"] else None, "/")


def bouw_post(p, vorige, volgende):
    tekst, tags = tekst_naar_html(p["caption"])
    figuren = "\n      ".join(
        f'<figure><img src="../beeld/{b["groot"]}" alt="{html.escape(p["titel"])}, beeld {i + 1}" '
        f'width="{b["w"]}" height="{b["h"]}" loading="{"eager" if i == 0 else "lazy"}"></figure>'
        for i, b in enumerate(p["beelden"]))

    paar = ""
    if p["fout"] or p["goed"]:
        rijen = []
        if p["fout"]:
            rijen.append(f"<div><dt>Op de foto</dt><dd>{html.escape(p['fout'])}</dd></div>")
        if p["goed"]:
            rijen.append(f"<div><dt>Het ging over</dt><dd>{html.escape(p['goed'])}</dd></div>")
        paar = f'<dl class="paar">{"".join(rijen)}</dl>'

    rectificatie = ""
    if p.get("rectificatie"):
        rectificatie = (f'<p class="rectificatie"><strong>Aangepast.</strong> '
                        f'{html.escape(p["rectificatie"])}</p>')

    orgs = ", ".join(p["orgs"]) if p["orgs"] else "Ingezonden"
    tagblok = ""
    if tags:
        tagblok = '<div class="tags">' + "".join(
            f"<span>#{html.escape(t)}</span>" for t in dict.fromkeys(tags)) + "</div>"

    bronlink = ""
    if p.get("code"):
        bronlink = (f'<p class="bronlink"><a href="https://www.instagram.com/p/{p["code"]}/">'
                    f'Bekijk deze post op Instagram</a></p>')

    buren = []
    if volgende:
        buren.append(f'<a href="{volgende["slug"]}.html">&larr; Ouder<br><b>{html.escape(volgende["titel"])}</b></a>')
    if vorige:
        buren.append(f'<a class="r" href="{vorige["slug"]}.html">Nieuwer &rarr;<br><b>{html.escape(vorige["titel"])}</b></a>')

    inhoud = f"""<main class="wrap smal">
  <a class="terug" href="../index.html">&larr; Alle gevallen</a>
  <article>
    <h1>{html.escape(p['titel'])}</h1>
    <div class="regel">{datum_nl(p['datum'])} &middot; {html.escape(orgs)}</div>
    {paar}
    {rectificatie}
    {figuren}
    <div class="tekst">
      {tekst}
    </div>
    {tagblok}
    {bronlink}
  </article>
  <nav class="buren">
    {chr(10).join(buren)}
  </nav>
</main>

{VOET}"""

    return pagina(f"{p['titel']} · NatuurSpeld", samenvatting(p["caption"]), inhoud, "../",
                  p["beelden"][0]["groot"] if p["beelden"] else None, f"/post/{p['slug']}.html")


def main():
    posts = json.loads((CONTENT / "posts.json").read_text(encoding="utf-8"))
    posts.sort(key=lambda p: p["datum"], reverse=True)

    (WORTEL / "index.html").write_text(bouw_index(posts), encoding="utf-8")
    shutil.copyfile(CONTENT / "stijl.css", WORTEL / "stijl.css")

    postmap = WORTEL / "post"
    if postmap.exists():
        shutil.rmtree(postmap)
    postmap.mkdir()
    for i, p in enumerate(posts):
        vorige = posts[i - 1] if i > 0 else None
        volgende = posts[i + 1] if i + 1 < len(posts) else None
        (postmap / f"{p['slug']}.html").write_text(bouw_post(p, vorige, volgende), encoding="utf-8")

    vandaag = date.today().isoformat()
    urls = [f"  <url><loc>{SITE}/</loc><lastmod>{vandaag}</lastmod></url>"]
    urls += [f"  <url><loc>{SITE}/post/{p['slug']}.html</loc><lastmod>{p['datum']}</lastmod></url>"
             for p in posts]
    (WORTEL / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls) + "\n</urlset>\n", encoding="utf-8")
    (WORTEL / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")

    (WORTEL / "404.html").write_text(pagina(
        "Niet gevonden · NatuurSpeld",
        "Deze pagina bestaat niet.",
        f"""<main class="wrap smal">
  <header class="kop"><h1 class="merk">Niet gevonden</h1>
  <p>Deze pagina bestaat niet of niet meer.</p></header>
  <p><a href="/index.html">Naar alle gevallen</a></p>
</main>
{VOET}""", "", None, "/404.html"), encoding="utf-8")

    print(f"gebouwd: 1 index + {len(posts)} postpagina's + sitemap")


if __name__ == "__main__":
    main()
