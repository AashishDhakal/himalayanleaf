"""Editorial content and the Wikimedia photography stand-ins.

Everything here is copy, not data the client edits per-record — the four lots and
the quote requests are models; these are the fixed parts of the page.

LICENCE NOTE: every photograph below is CC BY-SA 4.0 from Wikimedia Commons and is
a STAND-IN. The licence is share-alike and requires the visible attribution these
templates render. Replace them with the client's own estate photography before the
site goes live commercially; the credits come off with them.
"""

COMMONS = "https://commons.wikimedia.org/wiki/Special:FilePath/{}?width={}"


def _commons(filename, width=1800):
    return COMMONS.format(filename, width)


def _timelapse(frames, hold):
    """Stamp each frame with the shared cycle length and its own start offset.

    Every frame runs the same keyframe track; staggering the delay by one hold
    is what makes them hand off in sequence.
    """
    cycle = hold * len(frames)
    return [dict(f, cycle=cycle, delay=i * hold) for i, f in enumerate(frames)]


# Hero: four estate frames cross-fading on a nine-second hold.
HERO_HOLD = 9
_HERO_FRAMES = [
    {"src": _commons("Kanyam_ilam,nepal.jpg", 2000), "alt": "Tea gardens above Kanyam, Ilam", "ox": 46, "oy": 52},
    {"src": _commons("Tea_garden_kanyam_ilam_Nepal.jpg", 2000), "alt": "Kanyam tea garden under cloud", "ox": 54, "oy": 46},
    {"src": _commons("Kanyam_hills_of_Queen,ilam_9.jpg", 2000), "alt": "The hills of Kanyam, Ilam", "ox": 50, "oy": 58},
    {"src": _commons("Beautiful_garden_ilam.jpg", 2000), "alt": "Ilam garden at first light", "ox": 44, "oy": 50},
]

# Estate: cloud and mist frames on an eight-second hold.
ESTATE_HOLD = 8
_ESTATE_FRAMES = [
    {"src": _commons("Kanyam_in_Clouds.jpg"), "alt": "Kanyam under cloud", "ox": 50, "oy": 54},
    {"src": _commons("Evening_and_cloud.jpg"), "alt": "Evening cloud over the gardens", "ox": 52, "oy": 48},
    {"src": _commons("Mist_vally_tea_industry.jpg"), "alt": "Mist in the tea valley", "ox": 48, "oy": 56},
    {"src": _commons("Tea_garden_kanyam_ilam_Nepal.jpg"), "alt": "Cloud clearing off the Kanyam garden", "ox": 54, "oy": 50},
]

HERO_FRAMES = _timelapse(_HERO_FRAMES, HERO_HOLD)
ESTATE_FRAMES = _timelapse(_ESTATE_FRAMES, ESTATE_HOLD)

ESTATE_FACTS = [
    ("1,400–2,100 m", "Elevation"),
    ("4", "Orthodox lots"),
    ("100%", "Hand-plucked"),
]

# The Ascent: three photographs handing off as the altitude counter climbs.
ASCENT_PHOTOS = [
    {"src": _commons("Kanyam_ilam,nepal.jpg"), "alt": "Lower gardens above Ilam bazaar", "at": 0.0},
    {"src": _commons("Tea_garden_views.jpg"), "alt": "Mid-slope gardens", "at": 0.36},
    {"src": _commons("An_evening_at_tea_garden_of_kanyam.jpg"), "alt": "The ridge at evening", "at": 0.72},
]

ASCENT_LINES = [
    (0.0, "The road out of Ilam bazaar"),
    (0.30, "Where the gardens begin"),
    (0.58, "Cloud sits here until eleven"),
    (0.82, "The oldest bushes on the ridge"),
]

ASCENT_BASE_M = 240
ASCENT_RISE_M = 1860

RITUAL = [
    ("I", "Warm the vessel", "Rinse pot and cups with the water you will brew with. Cold glass flattens the first infusion.", "30 seconds"),
    ("II", "Measure the leaf", "Three grams to 150 ml. Orthodox leaf is whole, so it needs room to open.", "3 g / 150 ml"),
    ("III", "Pour and wait", "Water off the boil for green and white, full boil for black. Watch the leaf unfurl rather than the clock.", "70–95 °C"),
    ("IV", "Cup and read", "Nose the wet leaf first, then the liquor. Note colour, body and how long the finish holds.", "Second infusion"),
]

OFFERS = [
    ("Bulk chests", "20 kg foil-lined chests, lot-sealed at the estate with garden mark and invoice-grade tasting notes.", "From 50 kg"),
    ("Retail tins", "The 50 g Himalayan Leaf tin, cased 24 units. Ready for shelf with no repacking.", "From 240 tins"),
    ("Private label", "Your artwork on our tins or your own packaging filled at origin. Plates and proofs in three weeks.", "From 500 units"),
]
