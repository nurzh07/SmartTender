import fakeredis

from app.core import cache as cache_module


def test_cache_set_and_get(monkeypatch):
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(cache_module, "redis_client", fake)

    cache_module.cache_set("test:key", {"a": 1}, ttl=60)
    assert cache_module.cache_get("test:key") == {"a": 1}
    assert cache_module.cache_get("missing") is None


def test_cache_key_patterns():
    assert cache_module.cache_key_tenders_active(2, "published") == (
        "tenders:active:page:2:status:published"
    )
    assert cache_module.cache_key_categories() == "categories:all"
