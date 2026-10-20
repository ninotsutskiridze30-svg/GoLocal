"""The five real-source poster examples stay linked to their reviewed records."""

import hashlib
import json
from pathlib import Path

from datetime import date

from scripts.evaluate_posters import compare, evaluate
from test_poster_extraction import event, extraction, f, items


ROOT = Path(__file__).resolve().parents[1]
POSTERS = ROOT / "data" / "posters"


def test_all_five_reference_images_are_present_and_unchanged():
    corpus = json.loads((POSTERS / "posters.json").read_text(encoding="utf-8"))
    assert len(corpus["posters"]) == 5
    assert sum(len(poster["events"]) for poster in corpus["posters"]) == 6
    for poster in corpus["posters"]:
        image = POSTERS / poster["image_file"]
        assert image.is_file()
        assert hashlib.sha256(image.read_bytes()).hexdigest().upper() == poster["image_sha256"]


def test_reference_exposes_unprinted_years_and_all_animation_films():
    corpus = json.loads((POSTERS / "posters.json").read_text(encoding="utf-8"))
    by_id = {poster["poster_id"]: poster for poster in corpus["posters"]}
    assert sum(poster["events"][0]["date_iso"] is None
               for poster in corpus["posters"][:4]) == 4
    films = set(by_id["music-of-animation"]["events"][0]["films_named_on_poster"])
    assert len(films) == 12
    assert {"The Lion King", "Toy Story", "Coco", "The Little Mermaid", "Frozen"} <= films


def test_evaluation_catches_invented_year_url_and_missing_films():
    corpus = json.loads((POSTERS / "posters.json").read_text(encoding="utf-8"))
    reference = next(p for p in corpus["posters"] if p["poster_id"] == "music-of-animation")
    observed_event = event(reference["events"][0]["title"])
    observed_event.date_iso = f("2026-10-22", "22 October 2026", 0.95)
    observed_event.displayed_time = f("17:00", "17:00", 0.95)
    observed_event.venue = f(reference["events"][0]["venue"], reference["events"][0]["venue"], 0.95)
    observed_event.films_named_on_poster = items(["Frozen"], "Frozen", 0.95)
    poster = extraction([observed_event])
    poster.source_url = f("https://example.com/invented", "https://example.com/invented", 0.95)
    issues = compare(reference, poster)["issues"]
    assert any("date_iso" in issue for issue in issues)
    assert any("films_named_on_poster" in issue for issue in issues)
    assert any("source_url" in issue for issue in issues)


def test_evaluator_processes_all_five_images_and_six_sessions():
    corpus = json.loads((POSTERS / "posters.json").read_text(encoding="utf-8"))
    by_hash = {poster["image_sha256"]: poster for poster in corpus["posters"]}
    called = []

    def fake_extractor(image_bytes):
        reference = by_hash[hashlib.sha256(image_bytes).hexdigest().upper()]
        called.append(reference["poster_id"])
        sessions = []
        for source in reference["events"]:
            session = event(source["title"])
            for name in (
                "date_text", "date_iso", "displayed_time", "time_role",
                "doors_open_time", "venue", "city",
            ):
                value = source[name]
                setattr(session, name, f(value, value, 0.95) if value is not None else f())
            for name in (
                "performers", "special_guests", "lineup", "program_items",
                "films_named_on_poster",
            ):
                value = source[name]
                setattr(session, name, items(value, ", ".join(value), 0.95) if value else items())
            sessions.append(session)
        result = extraction(sessions)
        platform = reference["ticket_platform"]
        result.ticket_platform = f(platform, platform, 0.95) if platform else f()
        phone = reference["contact_phone"]
        result.contact_phone = f(phone, phone, 0.95) if phone else f()
        return result

    report = evaluate(corpus, POSTERS, today=date(2026, 10, 19), extractor=fake_extractor)
    assert report["posters_checked"] == 5
    assert len(called) == 5
    assert len(set(called)) == 5
    assert all(not row["issues"] for row in report["results"])
