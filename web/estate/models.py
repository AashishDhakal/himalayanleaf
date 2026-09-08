from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Tea(models.Model):
    """One of the four orthodox lots offered to buyers."""

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0, help_text="Lot number order, lowest first.")

    liquor = models.CharField(
        max_length=7,
        help_text="Hex colour of the brewed liquor. The page steeps into this on hover.",
    )
    tin = models.CharField(
        max_length=200,
        help_text="CSS background for the drawn tin, e.g. a linear-gradient().",
    )

    note = models.TextField(help_text="Tasting note shown on the card and the lot page.")
    grade = models.CharField(max_length=80)
    harvest = models.CharField(max_length=80)
    cup = models.CharField(max_length=80, help_text="Liquor colour and brewing guidance.")
    tonnage = models.CharField(max_length=80, help_text="Seasonal availability.")
    price = models.CharField(max_length=120, help_text="Indicative FOB price band.")

    leaf_photo = models.ImageField(
        upload_to="lots/",
        blank=True,
        help_text="Dry- or wet-leaf photograph for the lot page. Falls back to the stand-in below.",
    )
    leaf_photo_url = models.URLField(
        blank=True,
        help_text="Fallback photo URL used until a real leaf photograph is uploaded.",
    )
    leaf_credit = models.CharField(max_length=200, blank=True)
    leaf_credit_href = models.URLField(blank=True)

    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ("order", "name")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def lot_number(self):
        return f"{self.order + 1:02d}"

    @property
    def leaf_src(self):
        """Uploaded photograph wins; the Commons stand-in fills in until there is one."""
        if self.leaf_photo:
            return self.leaf_photo.url
        return self.leaf_photo_url

    @property
    def show_leaf_credit(self):
        """Credit belongs to the stand-in only — an uploaded photo carries no CC obligation."""
        return bool(self.leaf_credit and not self.leaf_photo)

    @property
    def specs(self):
        return [
            ("Grade", self.grade),
            ("Harvest", self.harvest),
            ("In the cup", self.cup),
            ("Availability", self.tonnage),
            ("Pricing", self.price),
        ]


class QuoteRequest(models.Model):
    """A completed run through the seven-step quote ceremony."""

    VOLUME_CHOICES = [
        ("50 – 100 kg", "50 – 100 kg"),
        ("100 – 500 kg", "100 – 500 kg"),
        ("500 kg – 1 tonne", "500 kg – 1 tonne"),
        ("Over 1 tonne", "Over 1 tonne"),
        ("Samples first", "Samples first"),
    ]
    PACKAGING_CHOICES = [
        ("20 kg bulk chests", "20 kg bulk chests"),
        ("50 g retail tins", "50 g retail tins"),
        ("Private label", "Private label"),
        ("Undecided", "Undecided"),
    ]
    TIMELINE_CHOICES = [
        ("Within a month", "Within a month"),
        ("This quarter", "This quarter"),
        ("Next flush", "Next flush"),
        ("Just exploring", "Just exploring"),
    ]

    reference = models.CharField(max_length=16, unique=True, editable=False)

    teas = models.ManyToManyField(Tea, related_name="quote_requests", blank=True)
    volume = models.CharField(max_length=40, choices=VOLUME_CHOICES, blank=True)
    packaging = models.CharField(max_length=40, choices=PACKAGING_CHOICES, blank=True)
    destination = models.CharField(max_length=120, blank=True)
    company = models.CharField(max_length=160, blank=True)
    role = models.CharField(max_length=160, blank=True, verbose_name="Name and role")
    email = models.EmailField(blank=True)
    timeline = models.CharField(max_length=40, choices=TIMELINE_CHOICES, blank=True)
    notes = models.TextField(blank=True)

    submitted_at = models.DateTimeField(default=timezone.now, editable=False)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-submitted_at",)

    def __str__(self):
        return f"{self.reference} · {self.company or self.email or 'unnamed'}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._next_reference()
        super().save(*args, **kwargs)

    @staticmethod
    def _next_reference():
        """HL-2601, HL-2602, … — sequential and human-readable on the phone."""
        last = QuoteRequest.objects.order_by("-id").values_list("reference", flat=True).first()
        seed = 2600
        if last and last.startswith("HL-") and last[3:].isdigit():
            seed = int(last[3:])
        return f"HL-{seed + 1}"
