from django.contrib import admin
from django.utils import timezone

from .models import QuoteRequest, Tea


@admin.register(Tea)
class TeaAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "grade", "harvest", "price", "is_published")
    list_editable = ("order", "is_published")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (None, {"fields": ("name", "slug", "order", "is_published")}),
        ("Colour", {"fields": ("liquor", "tin"), "description": "The liquor colour steeps the page on hover."}),
        ("Copy", {"fields": ("note", "grade", "harvest", "cup", "tonnage", "price")}),
        (
            "Leaf photograph",
            {
                "fields": ("leaf_photo", "leaf_photo_url", "leaf_credit", "leaf_credit_href"),
                "description": "Upload the estate's own photograph — it replaces the stand-in and its credit.",
            },
        ),
    )


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ("reference", "company", "email", "volume", "destination", "submitted_at", "answered")
    list_filter = ("volume", "packaging", "timeline", "submitted_at")
    search_fields = ("reference", "company", "role", "email", "destination", "notes")
    filter_horizontal = ("teas",)
    readonly_fields = ("reference", "submitted_at")
    actions = ("mark_answered",)

    @admin.display(boolean=True, description="Answered")
    def answered(self, obj):
        return obj.answered_at is not None

    @admin.action(description="Mark selected requests as answered")
    def mark_answered(self, request, queryset):
        updated = queryset.update(answered_at=timezone.now())
        self.message_user(request, f"{updated} request(s) marked answered.")
