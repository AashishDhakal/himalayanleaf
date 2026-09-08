import json

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from .content import (
    ASCENT_BASE_M,
    ASCENT_LINES,
    ASCENT_PHOTOS,
    ASCENT_RISE_M,
    ESTATE_FACTS,
    ESTATE_FRAMES,
    HERO_FRAMES,
    OFFERS,
    RITUAL,
)
from .models import QuoteRequest, Tea
from .quote_flow import (
    SESSION_KEY,
    build_steps,
    is_filled,
    next_label,
    summary_rows,
)

DEFAULT_LIQUOR = "#C98F2E"


def _teas():
    return list(Tea.objects.filter(is_published=True))


def _is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def _steam():
    """Seven wisps. `off` is the fixed spread the cursor lean is added to."""
    return [
        {
            "x": 16 + i * 40,
            "w": 10 + (i % 3) * 6,
            "dur": round(7 + (i % 4) * 1.6, 2),
            "delay": round(i * 0.85, 2),
            "off": (i - 3) * 10,
        }
        for i in range(7)
    ]


# ─── page ──────────────────────────────────────────────────────────────────────


@require_GET
def home(request):
    return render(request, "estate/home.html", _home_context())


def _home_context():
    teas = _teas()
    return {
        "teas": teas,
        "hero_frames": HERO_FRAMES,
        "estate_frames": ESTATE_FRAMES,
        "estate_facts": ESTATE_FACTS,
        "ascent_photos": ASCENT_PHOTOS,
        "ascent_lines": [
            {"at": at, "text": text, "metres": f"{ASCENT_BASE_M + round(at * ASCENT_RISE_M):,}"}
            for at, text in ASCENT_LINES
        ],
        "ascent_lines_data": [{"at": at, "text": text} for at, text in ASCENT_LINES],
        "ascent_base_m": ASCENT_BASE_M,
        "ascent_rise_m": ASCENT_RISE_M,
        "ritual": RITUAL,
        "offers": OFFERS,
        "hills": [
            {"colour": "#163024", "height": 34, "parallax": 0.02, "lean": 10, "scale": 1.00},
            {"colour": "#14382A", "height": 46, "parallax": 0.05, "lean": 24, "scale": 1.06},
            {"colour": "#0F2C21", "height": 60, "parallax": 0.09, "lean": 38, "scale": 1.12},
            {"colour": "#0A1B14", "height": 78, "parallax": 0.16, "lean": 52, "scale": 1.18},
        ],
        "steam": _steam(),
        "drift": [
            {
                "left": 4 + i * 12.5,
                "w": 7 + (i % 3) * 3,
                "h": 16 + (i % 4) * 6,
                "colour": "rgba(192,154,78,0.5)" if i % 2 else "rgba(122,160,120,0.45)",
                "dur": 26 + (i % 5) * 7,
                "delay": i * 3.4,
                "dx": (1 if i % 2 else -1) * (60 + i * 18),
                "spin": 300 + i * 90,
            }
            for i in range(8)
        ],
    }


# ─── lot sheet ─────────────────────────────────────────────────────────────────


@require_GET
def lot(request, slug):
    """A lot is a real URL. Over HTMX it comes back as the sliding sheet only."""
    teas = _teas()
    tea = get_object_or_404(Tea, slug=slug, is_published=True)
    index = next((i for i, t in enumerate(teas) if t.pk == tea.pk), 0)
    context = {"tea": tea, "next_tea": teas[(index + 1) % len(teas)] if teas else None}
    if _is_htmx(request):
        return render(request, "estate/partials/lot_sheet.html", context)
    context.update(_home_context())
    context["open_lot"] = tea
    return render(request, "estate/home.html", context)


@require_GET
def lot_close(request):
    """Empties the sheet container; the browser URL goes back to the estate."""
    if _is_htmx(request):
        return HttpResponse("")
    return HttpResponseRedirect(reverse("estate:home"))


# ─── quote ceremony ────────────────────────────────────────────────────────────


def _answers(request):
    return request.session.get(SESSION_KEY, {})


def _save(request, answers):
    request.session[SESSION_KEY] = answers
    request.session.modified = True


def _liquor_for(answers):
    """The ceremony brews in the colour of the first lot they picked."""
    picked = answers.get("teas") or []
    if picked:
        tea = Tea.objects.filter(name=picked[0]).first()
        if tea:
            return tea.liquor
    return DEFAULT_LIQUOR


def _stage_context(request, index, answers):
    teas = _teas()
    steps = build_steps([t.name for t in teas])
    index = max(0, min(index, len(steps) - 1))
    step = steps[index]
    filled = is_filled(step, answers)
    progress = index / (len(steps) - 1)

    ready = "Return to the estate" if step.is_done else "Send to the estate" if step.is_review else "Continue"

    return {
        "step": step,
        "step_index": index,
        "pips": [i <= index for i in range(len(steps))],
        "filled": filled,
        "can_back": index > 0 and not step.is_done,
        "next_label": next_label(step, filled),
        "ready_label": ready,
        "step_config": json.dumps(_step_config(step)),
        "form_fields": [
            {
                "key": f.key,
                "label": f.label,
                "placeholder": f.placeholder,
                "value": answers.get(f.key, ""),
                "type": "email" if f.key == "email" else "text",
                "autocomplete": {"company": "organization", "email": "email", "role": "name"}.get(f.key, "off"),
            }
            for f in step.fields
        ],
        "notes_value": answers.get("notes", ""),
        "selected": answers.get(step.key) or ([] if step.multi else ""),
        "summary": summary_rows(answers),
        "reference": answers.get("reference", ""),
        "progress": progress,
        "brew_label": "Infusion complete" if step.is_done else f"Steeping · {round(progress * 100)}%",
    }


def _step_config(step):
    """What Alpine needs to decide, live, whether Continue is lit."""
    return {
        "kind": step.kind,
        "multi": step.multi,
        "name": step.key,
        "keys": [f.key for f in step.fields],
    }


def _stage_response(request, index, answers):
    context = _stage_context(request, index, answers)
    response = render(request, "estate/partials/quote_stage.html", context)
    # The fill and glow live in the ceremony shell so their CSS transitions survive
    # the swap — Alpine picks the new values up from this trigger.
    response["HX-Trigger"] = json.dumps(
        {
            "hl-brew": {
                "progress": round(context["progress"], 4),
                "liquor": _liquor_for(answers),
                "done": context["step"].is_done,
            }
        }
    )
    return response


@require_GET
def quote_open(request):
    answers = _answers(request)
    if answers.get("reference"):  # a finished ceremony starts clean
        answers = {}
        _save(request, answers)
    lot_slug = request.GET.get("lot")
    if lot_slug:
        tea = Tea.objects.filter(slug=lot_slug, is_published=True).first()
        if tea:
            answers["teas"] = [tea.name]
            _save(request, answers)
    context = _stage_context(request, 0, answers)
    context["liquor"] = _liquor_for(answers)
    context["steam"] = _steam()
    if not _is_htmx(request):
        context.update(_home_context())
        context["open_quote"] = True
        return render(request, "estate/home.html", context)
    return render(request, "estate/partials/quote_shell.html", context)


@require_GET
def quote_close(request):
    if _is_htmx(request):
        return HttpResponse("")
    return HttpResponseRedirect(reverse("estate:home"))


@require_POST
def quote_step(request):
    answers = dict(_answers(request))
    teas = _teas()
    steps = build_steps([t.name for t in teas])

    try:
        index = int(request.POST.get("step", 0))
    except (TypeError, ValueError):
        index = 0
    index = max(0, min(index, len(steps) - 1))
    step = steps[index]
    action = request.POST.get("action", "next")

    # Record whatever this step collected first — including on Back, so stepping
    # backwards never throws away what they just typed.
    if action != "skip":
        if step.multi:
            answers[step.key] = request.POST.getlist(step.key)
        elif step.is_choice:
            value = request.POST.get(step.key, "")
            if value in step.options:
                answers[step.key] = value
        elif step.is_text:
            for f in step.fields:
                answers[f.key] = (request.POST.get(f.key) or "").strip()
        elif step.is_notes:
            answers["notes"] = (request.POST.get("notes") or "").strip()
        _save(request, answers)

    if action == "back":
        return _stage_response(request, index - 1, answers)

    if not is_filled(step, answers) and action != "skip":
        # Nothing valid arrived — re-render the same step rather than advancing.
        return _stage_response(request, index, answers)

    # Sending the review is the only write. Guard it so a double submit — a
    # double-click, or a resend of the same post — cannot file the request twice.
    if step.is_review and not answers.get("reference"):
        answers["reference"] = _persist(answers)
        _save(request, answers)

    return _stage_response(request, index + 1, answers)


def _persist(answers):
    quote = QuoteRequest.objects.create(
        volume=answers.get("volume", ""),
        packaging=answers.get("packaging", ""),
        destination=answers.get("destination", ""),
        company=answers.get("company", ""),
        role=answers.get("role", ""),
        email=answers.get("email", ""),
        timeline=answers.get("timeline", ""),
        notes=answers.get("notes", ""),
    )
    quote.teas.set(Tea.objects.filter(name__in=answers.get("teas") or []))
    return quote.reference
