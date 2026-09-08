# Himalayan Leaf

Django implementation of the Claude Design prototype in `../project/Himalayan Leaf.dc.html`.
Server-rendered templates, HTMX for the flows, Alpine for the motion. No build step.

## Running it

```bash
cd web
pip install -r requirements.txt
python manage.py migrate          # creates the four lots
python manage.py createsuperuser  # for /admin/
python manage.py runserver
```

Then http://127.0.0.1:8000/ — and http://127.0.0.1:8000/admin/ for the lots and the
incoming quote requests.

```bash
python manage.py test estate
```

## How it is put together

```
config/                 settings, urls
estate/
  models.py             Tea, QuoteRequest
  content.py            editorial copy + the photography stand-ins
  quote_flow.py         the seven-step ceremony, defined once
  views.py              page, lot sheet, ceremony steps
  templates/estate/     base, home, partials/
  static/estate/
    css/himalayan.css   all of the design's motion and layout
    js/himalayan.js     the Alpine components
    vendor/             htmx 2.0.4, Alpine 3.14.8 (vendored, no CDN)
```

**Who does what.** The prototype recomputed inline styles in JS on every pointer
move. Here CSS owns the geometry and only four numbers cross the JS boundary, as
custom properties on `:root`:

| property | range | drives |
| --- | --- | --- |
| `--lean` | −1 … 1 | steam lean, hill and ridge parallax, card tilt, the turning tin |
| `--mx` `--my` | 0 … 1 | the cursor drop, card tilt, tin rotation |
| `--scroll` | px | hero drift, hill parallax, the ghosted ILAM |

Section-scoped properties do the rest: `--p` on the Ascent (scroll progress),
`--steep-colour` / `--steep-x` on the collection (the hovered lot's liquor),
`--progress` / `--liquor` on the ceremony.

**HTMX** owns anything with server state. A lot is a real URL (`/lots/golden-tips/`)
that returns a full page normally and just the sheet over HTMX, so lots are
linkable and indexable. The quote ceremony posts one step at a time; the step
definitions and validation live in `quote_flow.py`, answers accumulate in the
session, and the review step writes a `QuoteRequest`.

The ceremony shell is never swapped — only the stage inside it — so the brew fill
keeps its CSS transition running from step to step. The server reports the new
progress on each response via an `HX-Trigger` (`hl-brew`) that Alpine picks up.

**Without JavaScript** every page still renders: the lot pages, the ceremony and
its steps all work as ordinary form posts. The animation is the enhancement.

`prefers-reduced-motion` drops the intro, the cursor drop, drifting leaves and the
pour, and freezes the timelapses on their first frame.

## Two things to settle with the client

**The photography is licensed stand-ins.** Every image is CC BY-SA 4.0 from
Wikimedia Commons. That licence is share-alike and requires the visible
attribution the templates render (hero, estate, ascent, lot pages, and the footer
credit block in `partials/photo_credits.html`). Fine for a pitch or staging site;
for the live commercial build the client should shoot their own estate photography
or buy licensed stock. Each lot has a `leaf_photo` upload field in the admin — an
uploaded photo replaces the stand-in *and* its credit automatically. The hero,
estate and ascent frames are in `content.py`.

**The commercial figures are placeholders** carried over from the prototype: the
50 kg minimum, the per-kg indicative price bands, the seasonal tonnages, the
"three weeks" for private-label proofs and the two-working-day reply. They are
seeded in `migrations/0002_seed_lots.py` and editable per lot in the admin.
Confirm each against what Himalayan Leaf actually offers before launch.

## Before deploying

`DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0` and `DJANGO_ALLOWED_HOSTS` are read from the
environment. With `DEBUG=0` you also need `collectstatic` and a real static/media
file server, and SQLite should become Postgres. Quote requests currently only land
in the database — if the client wants them emailed, that hooks into `_persist()`
in `views.py`.
