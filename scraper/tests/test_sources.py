"""Kaynak adaptörleri; ağ yok, httpx.MockTransport ile uydurma yanıtlar."""

import json
from datetime import date
from pathlib import Path
from typing import Any

import httpx

from collector.clean import EMAIL_MASK
from collector.http import PoliteClient
from collector.sources import arbeitnow, emscad, himalayas, hn, jobicy, remoteok, remotive

OCT_2026 = 1790812800  # 2026-10-01 00:00 UTC


def client_for(routes: dict[str, Any]) -> PoliteClient:
    def handler(request: httpx.Request) -> httpx.Response:
        key = request.url.path + (f"?{request.url.query.decode()}" if request.url.query else "")
        for prefix, body in routes.items():
            if key.startswith(prefix):
                return httpx.Response(200, json=body)
        return httpx.Response(404, json=None)

    return PoliteClient(delay_s=0, transport=httpx.MockTransport(handler))


def test_hn_reads_only_hiring_threads_and_never_the_author() -> None:
    routes = {
        "/v0/user/whoishiring.json": {"submitted": [3, 2, 1]},
        "/v0/item/3.json": {"id": 3, "title": "Ask HN: Freelancer? Seeking freelancer? (October 2026)", "kids": [99]},
        "/v0/item/2.json": {"id": 2, "title": "Ask HN: Who is hiring? (October 2026)", "kids": [10, 11, 12, 13, 14]},
        "/v0/item/10.json": {
            "id": 10,
            "by": "ornek_kullanici",
            "time": OCT_2026,
            "text": "Acme | Backend Engineer | Berlin | REMOTE (EU)<p>We build APIs with Python and PostgreSQL."
            " Write to jobs@acme.example",
        },
        "/v0/item/11.json": {"id": 11, "deleted": True},
        "/v0/item/12.json": {"id": 12, "dead": True, "text": "spam"},
        # İngilizce/Türkçe olmayan ilan alınmaz.
        "/v0/item/13.json": {
            "id": 13,
            "time": OCT_2026,
            "text": "Beta | Utvecklare<p>Vi söker en utvecklare till oss.",
        },
        # İş arayanın kendini tanıttığı yorum: kişisel veri, alınmaz.
        "/v0/item/14.json": {
            "id": 14,
            "time": OCT_2026,
            "text": "Location: Ankara<p>Remote: Yes<p>Willing to relocate: No<p>Technologies: React and Go for the web",
        },
    }
    postings = list(hn.fetch(client_for(routes), months=1))

    assert len(postings) == 1
    p = postings[0]
    assert p.external_id == "10"
    assert p.url == "https://news.ycombinator.com/item?id=10"
    assert p.company == "Acme"
    assert p.title_raw == "Acme | Backend Engineer | Berlin | REMOTE (EU)"
    assert p.location == "REMOTE (EU)"
    assert p.posted_at == date(2026, 10, 1)
    assert EMAIL_MASK in p.description_clean
    assert "ornek_kullanici" not in json.dumps(p.__dict__, default=str)


def test_himalayas_keeps_software_jobs_once() -> None:
    dev = {
        "guid": "https://himalayas.app/companies/acme/jobs/backend",
        "title": "Backend Developer",
        "companyName": "Acme",
        "parentCategories": ["Developer"],
        "locationRestrictions": ["Germany"],
        "description": "<p>You will run our Go services on Kubernetes.</p>",
        "pubDate": OCT_2026,
    }
    sales = {**dev, "guid": "https://himalayas.app/x/sales", "parentCategories": ["Sales"]}
    routes = {
        "/jobs/api/search?q=software+engineer&sort=recent&page=1": {"jobs": [dev, sales, dev]},
        "/jobs/api/search": {"jobs": []},  # diğer sayfalar ve sorgular: gerçek API gibi boş liste
    }
    postings = list(himalayas.fetch(client_for(routes), pages_per_query=2))

    assert [p.external_id for p in postings] == [dev["guid"]]
    assert postings[0].location == "Germany"
    assert postings[0].description_clean == "You will run our Go services on Kubernetes."


def test_remoteok_skips_legal_notice_and_non_software() -> None:
    job = {
        "id": "77",
        "position": "Frontend Engineer",
        "company": "Beta",
        "epoch": OCT_2026,
        # Remote OK açıklamaları HTML'i kaçışlı gönderiyor.
        "description": "&lt;p&gt;You will build the UI with React and TypeScript.&lt;/p&gt;",
        "url": "https://remoteok.com/remote-jobs/77",
    }
    routes = {
        "/api": [
            {"legal": "Please link back to Remote OK"},
            job,
            {**job, "id": "78", "position": "Marketing Student Assistant"},
        ]
    }
    postings = list(remoteok.fetch(client_for(routes)))
    assert [(p.external_id, p.title_raw, p.location) for p in postings] == [("77", "Frontend Engineer", "Remote")]
    assert postings[0].description_clean == "You will build the UI with React and TypeScript."


def test_remotive_parses_jobs() -> None:
    routes = {
        "/api/remote-jobs": {
            "jobs": [
                {
                    "id": 5,
                    "title": "Data Engineer",
                    "company_name": "Gamma",
                    "url": "https://remotive.com/j/5",
                    "candidate_required_location": "Worldwide",
                    "description": "<p>You will own our pipelines in Spark.</p>",
                    "publication_date": "2026-10-22T18:40:19",
                }
            ]
        }
    }
    postings = list(remotive.fetch(client_for(routes)))
    assert [(p.external_id, p.posted_at) for p in postings] == [("5", date(2026, 10, 22))]


def test_jobicy_follows_cursor_and_keeps_each_job_once() -> None:
    job = {
        "id": 7,
        "jobTitle": "Backend Engineer",
        "companyName": "Delta",
        "url": "https://jobicy.com/jobs/7",
        "jobGeo": "Europe",
        "jobDescription": "<p>You will build our APIs in Python and work with the team.</p>",
        "pubDate": "2026-10-31T17:05:04+00:00",
    }
    routes = {
        "/api/jobs?industry=engineering&count=100&cursor=abc": {"jobs": [{**job, "id": 8}], "nextCursor": None},
        "/api/jobs?industry=engineering": {"jobs": [job], "nextCursor": "abc"},
        "/api/jobs?industry=data-science": {"jobs": [job], "nextCursor": None},
        "/api/jobs": {"jobs": [], "nextCursor": None},
    }
    postings = list(jobicy.fetch(client_for(routes)))
    assert [(p.external_id, p.posted_at) for p in postings] == [("7", date(2026, 10, 31)), ("8", date(2026, 10, 31))]


def test_arbeitnow_decodes_description_and_stops_at_last_page() -> None:
    job = {
        "slug": "python-developer-berlin-1",
        "title": "Python Developer",
        "company_name": "Epsilon",
        "url": "https://www.arbeitnow.com/jobs/1",
        "location": "Berlin",
        "remote": False,
        "description": "&lt;p&gt;You will work with our team on the data platform.&lt;/p&gt;",
        "created_at": OCT_2026,
    }
    routes = {
        "/api/job-board-api?page=1": {
            "data": [job, {**job, "slug": "s", "title": "Sales Manager"}],
            "links": {"next": None},
        }
    }
    postings = list(arbeitnow.fetch(client_for(routes), pages=5))
    assert [(p.external_id, p.location, p.posted_at) for p in postings] == [
        ("python-developer-berlin-1", "Berlin", date(2026, 10, 1))
    ]
    assert "<p>" not in postings[0].description_clean and "&lt;" not in postings[0].description_clean


def test_emscad_filters_fraud_and_non_software(tmp_path: Path) -> None:
    csv_path = tmp_path / "fake_job_postings.csv"
    header = "job_id,title,location,description,requirements,function,industry,fraudulent\n"
    rows = [
        '1,Senior Python Developer,"US, NY",We build APIs for the web,3+ years of Python,Information Technology,'
        "Internet,0\n",
        "2,Sales Associate,TR,You will sell our products,,Sales,Internet,0\n",
        "3,Software Engineer,US,Too good to be true for you,,Engineering,Internet,1\n",
    ]
    csv_path.write_text(header + "".join(rows), encoding="utf-8")

    postings = list(emscad.fetch(csv_path))
    assert [p.external_id for p in postings] == ["1"]
    assert postings[0].description_clean == "We build APIs for the web\n\n3+ years of Python"
    assert postings[0].posted_at is None


def test_hn_skips_comments_already_in_the_database() -> None:
    # Gece toplaması kayıtlı yorumları tekrar istemez (T-034); 404 dönen route istenirse test düşer.
    routes = {
        "/v0/user/whoishiring.json": {"submitted": [2]},
        "/v0/item/2.json": {"id": 2, "title": "Ask HN: Who is hiring? (October 2026)", "kids": [10, 11]},
        "/v0/item/11.json": {
            "id": 11,
            "time": OCT_2026,
            "text": "Acme | Backend Engineer | Remote<p>We build APIs with Python and PostgreSQL.",
        },
    }
    postings = list(hn.fetch(client_for(routes), months=1, skip_ids={"10"}))
    assert [p.external_id for p in postings] == ["11"]
