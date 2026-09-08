"""The seven-step quote ceremony, defined once and driven from the session.

The prototype held these steps in component state. Here they live on the server so
the flow can be validated, persisted and changed without touching the templates.
"""

from dataclasses import dataclass, field
from typing import Callable, List

SESSION_KEY = "hl_quote"


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    placeholder: str


@dataclass(frozen=True)
class Step:
    key: str
    tag: str
    question: str
    hint: str
    kind: str = "choice"  # choice | text | notes | review | done
    multi: bool = False
    skippable: bool = False
    options: List[str] = field(default_factory=list)
    fields: List[Field] = field(default_factory=list)

    @property
    def is_choice(self):
        return self.kind == "choice"

    @property
    def is_text(self):
        return self.kind == "text"

    @property
    def is_notes(self):
        return self.kind == "notes"

    @property
    def is_review(self):
        return self.kind == "review"

    @property
    def is_done(self):
        return self.kind == "done"


def build_steps(tea_names: List[str]) -> List[Step]:
    return [
        Step(
            key="teas",
            tag="One of seven",
            question="Which lots interest you?",
            hint="Pick as many as you like. We can quote them together or separately.",
            multi=True,
            options=tea_names,
        ),
        Step(
            key="volume",
            tag="Two of seven",
            question="How much, to begin with?",
            hint="First orders start at 50 kg across any combination of lots.",
            options=["50 – 100 kg", "100 – 500 kg", "500 kg – 1 tonne", "Over 1 tonne", "Samples first"],
        ),
        Step(
            key="packaging",
            tag="Three of seven",
            question="How should it arrive?",
            hint="Bulk leaves the estate lot-sealed; tins arrive shelf-ready.",
            options=["20 kg bulk chests", "50 g retail tins", "Private label", "Undecided"],
        ),
        Step(
            key="destination",
            tag="Four of seven",
            question="Where are we shipping?",
            hint="Country is enough for now — it sets duty and freight.",
            kind="text",
            fields=[Field("destination", "Destination country", "Germany")],
        ),
        Step(
            key="company",
            tag="Five of seven",
            question="Who are we speaking with?",
            hint="So the quote reaches the right desk.",
            kind="text",
            fields=[
                Field("company", "Company", "Kessler Tea Import"),
                Field("role", "Your name and role", "Anna Kessler, Head of Buying"),
                Field("email", "Email", "anna@kesslertea.de"),
            ],
        ),
        Step(
            key="timeline",
            tag="Six of seven",
            question="When do you need it?",
            hint="Flush timing decides which lots we can promise.",
            options=["Within a month", "This quarter", "Next flush", "Just exploring"],
        ),
        Step(
            key="notes",
            tag="Seven of seven",
            question="Anything else?",
            hint="Optional. Certifications, blend intentions, sample sets.",
            kind="notes",
            skippable=True,
        ),
        Step(
            key="review",
            tag="Before you send",
            question="Read it back",
            hint="Change anything with Back, then send it to the estate.",
            kind="review",
        ),
        Step(
            key="done",
            tag="Steeped",
            question="Your request is with us",
            hint="We will come back with pricing, current availability and a sample set.",
            kind="done",
        ),
    ]


def is_filled(step: Step, answers: dict) -> bool:
    """Whether this step has enough in it for Continue to light up."""
    if step.multi:
        return bool(answers.get(step.key))
    if step.is_choice:
        return bool(answers.get(step.key))
    if step.is_text:
        return all((answers.get(f.key) or "").strip() for f in step.fields)
    return True


def summary_rows(answers: dict) -> List[tuple]:
    teas = answers.get("teas") or []
    contact = " · ".join(p for p in (answers.get("role"), answers.get("email")) if p)
    return [
        ("Lots", ", ".join(teas) or "Not stated"),
        ("Volume", answers.get("volume") or "Not stated"),
        ("Packaging", answers.get("packaging") or "Not stated"),
        ("Destination", answers.get("destination") or "Not stated"),
        ("Company", answers.get("company") or "Not stated"),
        ("Contact", contact or "Not stated"),
        ("Timeline", answers.get("timeline") or "Not stated"),
        ("Notes", answers.get("notes") or "None"),
    ]


def next_label(step: Step, filled: bool) -> str:
    if step.is_done:
        return "Return to the estate"
    if step.is_review:
        return "Send to the estate"
    return "Continue" if filled else "Choose to continue"
