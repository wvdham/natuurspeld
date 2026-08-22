#!/usr/bin/env python3
"""Zet een geplaatste NatuurSpeld-post in het archief op natuurspeld.nl.

Draait het hele staartje in één keer: beelden verkleinen, de post in
content/posts.json zetten, build.py draaien en desgewenst committen en pushen.

Bestaat de post al (zelfde --code, of zelfde --slug als er geen code is), dan
worden alleen de meegegeven velden bijgewerkt. Zo is dit ook het gereedschap
voor een correctie achteraf.

Voorbeeld:

    python3 nieuwe-post.py \\
      --code DcVgyPACGml --datum 2026-08-22 \\
      --titel "Sluipvlieg, geen wilde bij of zweefvlieg" \\
      --orgs Trouw \\
      --fout "Sluipvlieg" --goed "Wilde bij of zweefvlieg" \\
      --groep insecten \\
      --caption-bestand ~/caption.txt \\
      --beeld ~/slide1.png --beeld ~/slide2.png \\
      --push

Een correctie achteraf:

    python3 nieuwe-post.py --code DcVgyPACGml \\
      --caption-bestand ~/nieuwe-caption.txt \\
      --rectificatie "Natuurmonumenten heeft de tekst aangepast." --push
"""
import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

from PIL import Image

WORTEL = Path(__file__).resolve().parent
POSTS = WORTEL / "content" / "posts.json"
BEELD = WORTEL / "beeld"
GROEPEN = {"vogels", "zoogdieren", "insecten", "planten", "overig"}
GROOT, KLEIN = 1100, 560


def slugify(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return re.sub(r"-+", "-", t)[:60].strip("-")


def vrije_slug(basis, posts, eigen):
    bezet = {p["slug"] for p in posts if p is not eigen}
    slug, n = basis, 2
    while slug in bezet:
        slug, n = f"{basis}-{n}", n + 1
    return slug


def verklein(bron, slug, index):
    im = Image.open(bron).convert("RGB")
    namen = {}
    for maat, achtervoegsel, kwaliteit in ((GROOT, "", 79), (KLEIN, "-klein", 74)):
        kopie = im.copy()
        kopie.thumbnail((maat, maat), Image.LANCZOS)
        naam = f"{slug}-{index}{achtervoegsel}.jpg"
        kopie.save(BEELD / naam, "JPEG", quality=kwaliteit, optimize=True, progressive=True)
        namen["groot" if not achtervoegsel else "klein"] = naam
        if not achtervoegsel:
            namen["w"], namen["h"] = kopie.width, kopie.height
    return namen


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--code", default="", help="Instagram-shortcode; leeg als er niet op Instagram geplaatst is")
    a.add_argument("--slug", help="alleen nodig als er geen code is")
    a.add_argument("--datum", help="JJJJ-MM-DD")
    a.add_argument("--titel", help='bij voorkeur in de vorm "X, geen Y"')
    a.add_argument("--orgs", nargs="*", help="aangesproken organisaties; laat weg bij een anonieme bron")
    a.add_argument("--fout", help="wat er op de foto staat")
    a.add_argument("--goed", help="waar de tekst over ging")
    a.add_argument("--groep", choices=sorted(GROEPEN))
    a.add_argument("--caption-bestand", help="tekstbestand met de Instagram-caption")
    a.add_argument("--rectificatie", help="notitie als de aangesproken partij het heeft aangepast")
    a.add_argument("--beeld", action="append", default=[], help="beeldbestand, herhaalbaar, in volgorde")
    a.add_argument("--push", action="store_true", help="na het bouwen committen en pushen")
    args = a.parse_args()

    posts = json.loads(POSTS.read_text(encoding="utf-8"))

    bestaand = None
    if args.code:
        bestaand = next((p for p in posts if p.get("code") == args.code), None)
    if bestaand is None and args.slug:
        bestaand = next((p for p in posts if p["slug"] == args.slug), None)

    if bestaand is None:
        for veld in ("datum", "titel", "groep"):
            if not getattr(args, veld):
                sys.exit(f"--{veld} is verplicht voor een nieuwe post")
        if not args.beeld:
            sys.exit("minstens een --beeld is verplicht voor een nieuwe post")
        post = {"slug": "", "code": args.code, "datum": args.datum, "titel": args.titel,
                "orgs": args.orgs or [], "fout": args.fout or "", "goed": args.goed or "",
                "groep": args.groep, "caption": "", "beelden": []}
        posts.append(post)
        nieuw = True
    else:
        post, nieuw = bestaand, False

    for veld in ("datum", "titel", "fout", "goed", "groep", "code"):
        if getattr(args, veld):
            post[veld] = getattr(args, veld)
    if args.orgs is not None:
        post["orgs"] = args.orgs
    if args.rectificatie:
        post["rectificatie"] = args.rectificatie
    if args.caption_bestand:
        post["caption"] = Path(args.caption_bestand).expanduser().read_text(encoding="utf-8").strip()
    if not post["caption"]:
        sys.exit("de post heeft geen caption; geef --caption-bestand mee")

    post["slug"] = vrije_slug(args.slug or slugify(post["titel"]), posts, post)

    if args.beeld:
        BEELD.mkdir(exist_ok=True)
        for oud in post["beelden"]:
            for naam in (oud["groot"], oud["klein"]):
                (BEELD / naam).unlink(missing_ok=True)
        post["beelden"] = [verklein(Path(b).expanduser(), post["slug"], i + 1)
                           for i, b in enumerate(args.beeld)]
    if not post["beelden"]:
        sys.exit("de post heeft geen beelden; geef --beeld mee")

    posts.sort(key=lambda p: p["datum"], reverse=True)
    POSTS.write_text(json.dumps(posts, ensure_ascii=False, indent=1), encoding="utf-8")
    subprocess.run([sys.executable, "build.py"], cwd=WORTEL, check=True)

    print(f"{'toegevoegd' if nieuw else 'bijgewerkt'}: {post['slug']} "
          f"({len(post['beelden'])} beeld{'en' if len(post['beelden']) > 1 else ''})")
    print(f"lokaal te bekijken: post/{post['slug']}.html")

    if args.push:
        boodschap = (f"Archief: {post['titel']}" if nieuw
                     else f"Archief: {post['titel']} bijgewerkt")
        subprocess.run(["git", "add", "-A"], cwd=WORTEL, check=True)
        subprocess.run(["git", "commit", "-q", "-m", boodschap], cwd=WORTEL, check=True)
        subprocess.run(["git", "push", "-q", "origin", "main"], cwd=WORTEL, check=True)
        print(f"gepusht, over een minuut live op https://natuurspeld.nl/post/{post['slug']}.html")
    else:
        print("nog niet gepusht; draai opnieuw met --push, of push met de hand")


if __name__ == "__main__":
    main()
