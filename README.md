# natuurspeld.nl

Doorverwijzing van natuurspeld.nl naar het Instagram-account
[@natuurspeld](https://www.instagram.com/natuurspeld/).

Statisch gehost op GitHub Pages. `index.html` en `404.html` zijn identiek, zodat
elk pad op het domein bij Instagram uitkomt. De doorverwijzing gebeurt via
`window.location.replace()` met een `meta refresh` als vangnet; wie beide blokkeert
krijgt een knop te zien.

## Aanpassen

Bestemming wijzigen: pas de URL aan in `index.html` (vier plekken: `canonical`,
`meta refresh`, `script` en de knop) en kopieer het bestand daarna weer naar
`404.html`.

Wil je hier later een echte pagina van maken (bijvoorbeeld een linkhub naar
Instagram, Facebook en LinkedIn), dan vervang je `index.html` en laat je de
DNS ongemoeid.

## DNS

Apex A/AAAA staan op de GitHub Pages-adressen, `www` is een CNAME naar
`wvdham.github.io`. Beheerd bij Mijndomein.
