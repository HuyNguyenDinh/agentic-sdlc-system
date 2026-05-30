import pytest
from src.core.services.knowledge_binding_resolver import (
    KnowledgeBindingResolver,
    KnowledgeBinding,
    ResolutionMode,
    ResolverStats
)


class TestKnowledgeBindingResolver:
    def setup_method(self):
        self.resolver = KnowledgeBindingResolver()
        self.test_provider_calls = []

        def test_provider(binding: KnowledgeBinding):
            self.test_provider_calls.append(binding.key)
            return f"value_{binding.key}"

        self.resolver.register_provider("test", test_provider)

    def test_prefetch_mode(self):
        bindings = [
            KnowledgeBinding("key1", "test"),
            KnowledgeBinding("key2", "test")
        ]

        self.resolver.prefetch(bindings)

        assert self.resolver.resolve("key1", ResolutionMode.PREFETCH) == "value_key1"
        assert self.resolver.resolve("key2", ResolutionMode.PREFETCH) == "value_key2"
        assert len(self.test_provider_calls) == 2
        assert self.resolver.get_stats().prefetch_count == 2

        with pytest.raises(ValueError):
            self.resolver.resolve("not_prefetched", ResolutionMode.PREFETCH)

    def test_on_demand_mode(self):
        binding = KnowledgeBinding("key1", "test")
        self.resolver._cache["key1"] = self.resolver._cache.get("key1", None)

        value = self.resolver.resolve("key1", ResolutionMode.ON_DEMAND)

        assert value == "value_key1"
        assert len(self.test_provider_calls) == 1
        assert self.resolver.get_stats().on_demand_count == 1

        # second call uses cache
        value2 = self.resolver.resolve("key1", ResolutionMode.ON_DEMAND)
        assert value2 == "value_key1"
        assert len(self.test_provider_calls) == 1
        assert self.resolver.get_stats().cache_hits == 1

    def test_implicit_mode(self):
        binding = KnowledgeBinding("key1", "test")

        value = self.resolver.resolve("key1", ResolutionMode.IMPLICIT)

        assert value == "value_key1"
        assert len(self.test_provider_calls) == 1
        assert self.resolver.get_stats().implicit_count == 1

    def test_cache_behavior(self):
        binding = KnowledgeBinding("key1", "test")

        # first miss
        v1 = self.resolver.resolve("key1")
        assert self.resolver.get_stats().cache_misses == 1

        # second hit
        v2 = self.resolver.resolve("key1")
        assert self.resolver.get_stats().cache_hits == 1
        assert self.resolver.get_stats().cache_misses == 1
        assert v1 == v2

    def test_invalidate(self):
        binding = KnowledgeBinding("key1", "test")
        self.resolver.prefetch([binding])

        assert "key1" in self.resolver._cache

        self.resolver.invalidate("key1")

        assert "key1" not in self.resolver._cache

        # refetch on next resolve
        v = self.resolver.resolve("key1")
        assert v == "value_key1"
        assert len(self.test_provider_calls) == 2

    def test_clear_cache(self):
        bindings = [KnowledgeBinding(f"key{i}", "test") for i in range(5)]
        self.resolver.prefetch(bindings)

        assert len(self.resolver._cache) == 5

        self.resolver.clear_cache()

        assert len(self.resolver._cache) == 0
        assert len(self.resolver._prefetched) == 0

    def test_resolve_all(self):
        keys = ["key1", "key2", "key3"]
        results = self.resolver.resolve_all(keys)

        assert len(results) == 3
        assert results["key1"] == "value_key1"
        assert results["key2"] == "value_key2"
        assert results["key3"] == "value_key3"

    def test_unknown_provider(self):
        binding = KnowledgeBinding("key1", "unknown_provider")

        with pytest.raises(ValueError):
            self.resolver.prefetch([binding])
