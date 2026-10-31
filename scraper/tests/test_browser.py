from urllib.robotparser import RobotFileParser

import pytest

from collector.browser import BrowserBlockedError, PageFetcher
from collector.sources import pythonorg

LIST_PAGE = """<ol class="list-recent-jobs list-row-container menu"><li>
<h2 class="listing-company"><span class="listing-company-name"><span class="listing-new">New</span>
<a href="/jobs/42/">Senior Python &amp; Data Engineer</a><br/>
    Delta Labs
</span><span class="listing-location"><a href="/jobs/location/x/" title="More">London, UK</a></span></h2>
<span class="listing-posted">Posted: <time datetime="2026-10-23T22:34:52.166674+00:00">23 October</time></span>
</li></ol>"""
DETAIL_PAGE = """<div class="job-description"><h2>Job Description</h2><p>You will build our APIs in Python and
work with the team on the data platform.</p><h2>Contact Info</h2><ul><li>Contact: Jane Roe</li>
<li>E-mail contact: jane@example.com</li></ul></div><!-- end .job-post-content -->"""


def robots(*lines: str) -> RobotFileParser:
    parser = RobotFileParser()
    parser.parse(lines)
    return parser


def fetcher(pages: dict[str, list[tuple[int, str]]], *rules: str) -> PageFetcher:
    def open_page(url: str) -> tuple[int, str]:
        return pages[url].pop(0)

    return PageFetcher(open_page, robots("User-agent: *", *rules), jitter=(0, 0))


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("collector.browser.time.sleep", lambda _: None)


def test_pythonorg_reads_list_and_detail_without_contact_block() -> None:
    pages = fetcher(
        {
            "https://www.python.org/jobs/": [(200, LIST_PAGE)],
            "https://www.python.org/jobs/42/": [(200, DETAIL_PAGE)],
        }
    )
    [posting] = pythonorg.fetch(pages)
    assert (posting.external_id, posting.title_raw, posting.company, posting.location) == (
        "42",
        "Senior Python & Data Engineer",
        "Delta Labs",
        "London, UK",
    )
    assert str(posting.posted_at) == "2026-10-23"
    assert "APIs in Python" in posting.description_clean
    assert "Jane" not in posting.description_clean and "jane@" not in posting.description_clean


def test_pythonorg_skips_known_jobs_without_opening_them() -> None:
    pages = fetcher({"https://www.python.org/jobs/": [(200, LIST_PAGE)]})
    assert list(pythonorg.fetch(pages, skip_ids={"42"})) == []
    assert pages.requests == 1


def test_retries_temporary_errors_then_succeeds() -> None:
    pages = fetcher({"https://x.test/a": [(503, ""), (429, ""), (200, "tamam")]})
    assert pages.get("https://x.test/a") == "tamam"
    assert pages.requests == 3


def test_timeout_is_retried() -> None:
    calls = iter([TimeoutError(), (200, "tamam")])

    def open_page(url: str) -> tuple[int, str]:
        result = next(calls)
        if isinstance(result, Exception):
            raise result
        return result

    assert PageFetcher(open_page, robots(), jitter=(0, 0)).get("https://x.test/a") == "tamam"


def test_forbidden_page_is_not_retried() -> None:
    pages = fetcher({"https://x.test/a": [(403, "")]})
    with pytest.raises(BrowserBlockedError):
        pages.get("https://x.test/a")
    assert pages.requests == 1


def test_robots_disallow_stops_before_any_request() -> None:
    pages = fetcher({}, "Disallow: /jobs/")
    with pytest.raises(BrowserBlockedError):
        pages.get("https://x.test/jobs/1/")
    assert pages.requests == 0


def test_waits_between_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    waits: list[float] = []
    monkeypatch.setattr("collector.browser.time.sleep", waits.append)
    pages = PageFetcher(lambda url: (200, ""), robots(), jitter=(3, 5))
    pages.get("https://x.test/a")
    pages.get("https://x.test/b")
    assert 2.9 < waits[-1] <= 5
