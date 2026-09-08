"""Seed the four lots the client currently offers.

Commercial figures (50 kg minimum, per-kg bands, seasonal tonnages) came across from
the design as placeholders — confirm them with the client and edit in the admin.
"""

from django.db import migrations

LEAF_STANDIN = "https://commons.wikimedia.org/wiki/Special:FilePath/Ilam_green.jpg?width=1800"
LEAF_CREDIT = "Ilam tea bushes · Hari gurung77, Wikimedia Commons, CC BY-SA 4.0"
LEAF_CREDIT_HREF = "https://commons.wikimedia.org/wiki/File:Ilam_green.jpg"

LOTS = [
    {
        "name": "Sencha Green",
        "slug": "sencha-green",
        "order": 0,
        "liquor": "#8FA83C",
        "tin": "linear-gradient(90deg, #123A2A, #1E5E42 45%, #0D2E21)",
        "note": "Steamed in the Japanese manner at 1,750 m. Vegetal, sweet grass, a clean marine finish.",
        "grade": "Steamed green, first flush",
        "harvest": "March – April",
        "cup": "Pale jade, 60 s at 70 °C",
        "tonnage": "Up to 900 kg per season",
        "price": "Indicative $46 – $58 / kg FOB Kathmandu",
    },
    {
        "name": "Silver Tips",
        "slug": "silver-tips",
        "order": 1,
        "liquor": "#D8C98A",
        "tin": "linear-gradient(90deg, #8E9296, #DDE0E2 45%, #7E8286)",
        "note": "Unopened buds plucked at dawn, withered in shade. Honeysuckle, melon, almost weightless.",
        "grade": "White, bud only",
        "harvest": "Late March",
        "cup": "Pale champagne, 4 min at 80 °C",
        "tonnage": "Up to 180 kg per season",
        "price": "Indicative $190 – $240 / kg FOB Kathmandu",
    },
    {
        "name": "Golden Tips",
        "slug": "golden-tips",
        "order": 2,
        "liquor": "#C98F2E",
        "tin": "linear-gradient(90deg, #9A7420, #E8C46B 45%, #8E6A1C)",
        "note": "Golden-tipped second flush, slow oxidised. Stone fruit, muscatel, warm bread crust.",
        "grade": "Orthodox black, FTGFOP1",
        "harvest": "May – June",
        "cup": "Amber, 3 min at 90 °C",
        "tonnage": "Up to 1,200 kg per season",
        "price": "Indicative $72 – $94 / kg FOB Kathmandu",
    },
    {
        "name": "Ruby Black",
        "slug": "ruby-black",
        "order": 3,
        "liquor": "#8E2A20",
        "tin": "linear-gradient(90deg, #171512, #33302B 45%, #121110)",
        "note": "Autumn flush, fully oxidised in cool mountain air. Cocoa, dark cherry, long malty tail.",
        "grade": "Orthodox black, autumnal",
        "harvest": "October – November",
        "cup": "Deep russet, 4 min at 95 °C",
        "tonnage": "Up to 1,500 kg per season",
        "price": "Indicative $54 – $68 / kg FOB Kathmandu",
    },
]


def seed(apps, schema_editor):
    Tea = apps.get_model("estate", "Tea")
    for lot in LOTS:
        Tea.objects.update_or_create(
            slug=lot["slug"],
            defaults={
                **lot,
                "leaf_photo_url": LEAF_STANDIN,
                "leaf_credit": LEAF_CREDIT,
                "leaf_credit_href": LEAF_CREDIT_HREF,
                "is_published": True,
            },
        )


def unseed(apps, schema_editor):
    Tea = apps.get_model("estate", "Tea")
    Tea.objects.filter(slug__in=[lot["slug"] for lot in LOTS]).delete()


class Migration(migrations.Migration):
    dependencies = [("estate", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
