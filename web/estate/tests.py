from django.test import TestCase
from django.urls import reverse

from .models import QuoteRequest, Tea

HTMX = {"HTTP_HX_REQUEST": "true"}


class PageTests(TestCase):
    def test_home_renders_the_four_seeded_lots(self):
        response = self.client.get(reverse("estate:home"))
        self.assertEqual(response.status_code, 200)
        for name in ["Sencha Green", "Silver Tips", "Golden Tips", "Ruby Black"]:
            self.assertContains(response, name)

    def test_home_carries_the_photo_attribution(self):
        """CC BY-SA 4.0 is share-alike — the credits must render on the page."""
        response = self.client.get(reverse("estate:home"))
        self.assertContains(response, "CC BY-SA 4.0")
        self.assertContains(response, "Hari gurung77")

    def test_lot_has_its_own_url(self):
        response = self.client.get(reverse("estate:lot", args=["golden-tips"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "FTGFOP1")
        self.assertContains(response, "hl-header")  # a full page, not a fragment

    def test_lot_over_htmx_is_the_sheet_only(self):
        response = self.client.get(reverse("estate:lot", args=["golden-tips"]), **HTMX)
        self.assertContains(response, "hl-sheet")
        self.assertNotContains(response, "hl-header")

    def test_unpublished_lot_is_hidden(self):
        Tea.objects.filter(slug="ruby-black").update(is_published=False)
        self.assertEqual(self.client.get(reverse("estate:lot", args=["ruby-black"])).status_code, 404)
        self.assertNotContains(self.client.get(reverse("estate:home")), "Ruby Black")

    def test_close_is_not_read_as_a_lot_slug(self):
        response = self.client.get(reverse("estate:lot_close"), **HTMX)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")


class QuoteCeremonyTests(TestCase):
    def open(self, **params):
        url = reverse("estate:quote_open")
        if params:
            url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
        return self.client.get(url, **HTMX)

    def step(self, index, **data):
        return self.client.post(reverse("estate:quote_step"), {"step": index, **data}, **HTMX)

    def test_opens_on_step_one(self):
        response = self.open()
        self.assertContains(response, "Which lots interest you?")
        self.assertContains(response, "One of seven")

    def test_opening_from_a_lot_preselects_it(self):
        response = self.open(lot="silver-tips")
        self.assertEqual(self.client.session["hl_quote"]["teas"], ["Silver Tips"])
        self.assertContains(response, "checked")

    def test_a_step_records_its_answer_and_advances(self):
        response = self.step(0, teas=["Golden Tips", "Ruby Black"], action="next")
        self.assertEqual(self.client.session["hl_quote"]["teas"], ["Golden Tips", "Ruby Black"])
        self.assertContains(response, "How much, to begin with?")

    def test_an_empty_step_does_not_advance(self):
        response = self.step(0, action="next")
        self.assertContains(response, "Which lots interest you?")

    def test_text_step_requires_every_field(self):
        answer = {"company": "Kessler Tea Import", "role": "", "email": "anna@kesslertea.de"}
        self.assertContains(self.step(4, action="next", **answer), "Who are we speaking with?")

    def test_back_keeps_what_was_just_typed(self):
        self.step(0, teas=["Silver Tips"], action="next")
        response = self.step(3, destination="Germany", action="back")
        self.assertEqual(self.client.session["hl_quote"]["destination"], "Germany")
        self.assertContains(response, "How should it arrive?")

    def test_notes_can_be_skipped(self):
        response = self.step(6, action="skip")
        self.assertContains(response, "Read it back")

    def test_the_brew_progress_rides_along_on_the_response(self):
        response = self.step(0, teas=["Ruby Black"], action="next")
        self.assertIn("hl-brew", response["HX-Trigger"])
        self.assertIn("#8E2A20", response["HX-Trigger"])  # brews in that lot's liquor

    def test_sending_the_review_persists_the_request(self):
        self.step(0, teas=["Golden Tips"], action="next")
        self.step(1, volume="100 – 500 kg", action="next")
        self.step(2, packaging="Private label", action="next")
        self.step(3, destination="Germany", action="next")
        self.step(4, company="Kessler Tea Import", role="Anna Kessler, Head of Buying",
                  email="anna@kesslertea.de", action="next")
        self.step(5, timeline="Next flush", action="next")
        self.step(6, notes="Organic certification needed.", action="next")
        response = self.step(7, action="next")  # the review

        quote = QuoteRequest.objects.get()
        self.assertEqual(quote.company, "Kessler Tea Import")
        self.assertEqual(quote.destination, "Germany")
        self.assertEqual(quote.timeline, "Next flush")
        self.assertEqual([t.name for t in quote.teas.all()], ["Golden Tips"])
        self.assertContains(response, "Your request is with us")
        self.assertContains(response, quote.reference)

    def test_sending_the_review_twice_files_one_request(self):
        self.step(0, teas=["Silver Tips"], action="next")
        self.step(7, action="next")
        self.step(7, action="next")  # double submit
        self.assertEqual(QuoteRequest.objects.count(), 1)

    def test_a_finished_ceremony_starts_clean_next_time(self):
        session = self.client.session
        session["hl_quote"] = {"reference": "HL-2601", "destination": "Germany"}
        session.save()
        self.open()
        self.assertEqual(self.client.session["hl_quote"], {})


class ReferenceTests(TestCase):
    def test_references_are_sequential(self):
        first = QuoteRequest.objects.create()
        second = QuoteRequest.objects.create()
        self.assertEqual(first.reference, "HL-2601")
        self.assertEqual(second.reference, "HL-2602")


class LeafPhotoTests(TestCase):
    def test_standin_credit_shows_until_a_real_photo_is_uploaded(self):
        tea = Tea.objects.get(slug="sencha-green")
        self.assertTrue(tea.show_leaf_credit)
        self.assertIn("Ilam_green", tea.leaf_src)
