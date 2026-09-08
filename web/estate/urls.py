from django.urls import path

from . import views

app_name = "estate"

urlpatterns = [
    path("", views.home, name="home"),
    # "close" before the slug route — it would otherwise match as a lot slug.
    path("lots/close/", views.lot_close, name="lot_close"),
    path("lots/<slug:slug>/", views.lot, name="lot"),
    path("quote/", views.quote_open, name="quote_open"),
    path("quote/close/", views.quote_close, name="quote_close"),
    path("quote/step/", views.quote_step, name="quote_step"),
]
