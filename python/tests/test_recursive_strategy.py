"""Unit tests for RecursiveCrawlStrategy domain filtering helpers."""
from src.server.services.crawling.strategies.recursive import RecursiveCrawlStrategy


def test_normalize_netloc_handles_default_ports_and_trailing_dot():
    strategy = RecursiveCrawlStrategy(crawler=None, markdown_generator=None)

    assert strategy._normalize_netloc("https://docs.example.com:443/path") == "docs.example.com"
    assert strategy._normalize_netloc("http://docs.example.com:80/path") == "docs.example.com"
    assert strategy._normalize_netloc("https://docs.example.com./path") == "docs.example.com"
    assert strategy._normalize_netloc("https://docs.example.com:8443/path") == "docs.example.com:8443"


def test_allowed_domain_filtering_multiple_start_domains():
    strategy = RecursiveCrawlStrategy(crawler=None, markdown_generator=None)

    allowed_domains = strategy._build_allowed_domains(
        [
            "https://docs.example.com/",
            "https://api.example.com:443/v1/",
        ]
    )

    assert strategy._is_allowed_domain("https://docs.example.com/guide", allowed_domains) is True
    assert strategy._is_allowed_domain("https://api.example.com/status", allowed_domains) is True
    assert strategy._is_allowed_domain("https://api.example.com:443/health", allowed_domains) is True
    assert strategy._is_allowed_domain("https://sub.docs.example.com/", allowed_domains) is False
    assert strategy._is_allowed_domain("/relative/path", allowed_domains) is False
