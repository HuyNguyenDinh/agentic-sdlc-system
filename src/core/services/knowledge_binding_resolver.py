from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class ResolutionMode(enum.Enum):
    PREFETCH = "prefetch"
    ON_DEMAND = "on_demand"
    IMPLICIT = "implicit"


@dataclass(frozen=True)
class KnowledgeBinding:
    key: str
    provider: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolvedKnowledge:
    binding: KnowledgeBinding
    value: Any
    resolved_at: float
    ttl: Optional[float] = None


@dataclass
class ResolverStats:
    prefetch_count: int = 0
    on_demand_count: int = 0
    implicit_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0


class KnowledgeBindingResolver:
    def __init__(self):
        self._cache: Dict[str, ResolvedKnowledge] = {}
        self._prefetched: Set[str] = set()
        self._providers: Dict[str, Callable[[KnowledgeBinding], Any]] = {}
        self._stats = ResolverStats()

    def register_provider(self, name: str, fetcher: Callable[[KnowledgeBinding], Any]) -> None:
        self._providers[name] = fetcher

    def prefetch(self, bindings: List[KnowledgeBinding]) -> None:
        for binding in bindings:
            if binding.key in self._prefetched:
                continue
            value = self._fetch_binding(binding)
            self._cache[binding.key] = ResolvedKnowledge(
                binding=binding,
                value=value,
                resolved_at=self._now()
            )
            self._prefetched.add(binding.key)
            self._stats.prefetch_count += 1

    def resolve(self, key: str, mode: ResolutionMode = ResolutionMode.ON_DEMAND) -> Any:
        if key in self._cache:
            self._stats.cache_hits += 1
            return self._cache[key].value

        self._stats.cache_misses += 1

        if mode == ResolutionMode.PREFETCH:
            raise ValueError(f"Binding {key} not prefetched")

        binding = self._find_binding(key)
        if not binding:
            raise KeyError(f"No knowledge binding found for {key}")

        value = self._fetch_binding(binding)
        self._cache[key] = ResolvedKnowledge(
            binding=binding,
            value=value,
            resolved_at=self._now()
        )

        if mode == ResolutionMode.ON_DEMAND:
            self._stats.on_demand_count += 1
        elif mode == ResolutionMode.IMPLICIT:
            self._stats.implicit_count += 1

        return value

    def resolve_all(self, keys: List[str], mode: ResolutionMode = ResolutionMode.ON_DEMAND) -> Dict[str, Any]:
        results = {}
        for key in keys:
            results[key] = self.resolve(key, mode)
        return results

    def get_stats(self) -> ResolverStats:
        return self._stats

    def clear_cache(self) -> None:
        self._cache.clear()
        self._prefetched.clear()

    def invalidate(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]
        if key in self._prefetched:
            self._prefetched.remove(key)

    def _fetch_binding(self, binding: KnowledgeBinding) -> Any:
        if binding.provider not in self._providers:
            raise ValueError(f"No provider registered for {binding.provider}")
        return self._providers[binding.provider](binding)

    def _find_binding(self, key: str) -> Optional[KnowledgeBinding]:
        for cached in self._cache.values():
            if cached.binding.key == key:
                return cached.binding
        return None

    def _now(self) -> float:
        import time
        return time.time()
