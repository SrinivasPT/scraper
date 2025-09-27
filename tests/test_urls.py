from regscraper.utils.urls import classify_url


def test_classify_url():
    assert classify_url("https://www.sec.gov/newsroom/press-releases") == "html"
    assert classify_url("https://www.bis.org/press/p250710.htm") == "html"
    assert (
        classify_url("https://www.sec.gov/files/rules/concept/2025/33-11391.pdf")
        == "pdf"
    )
