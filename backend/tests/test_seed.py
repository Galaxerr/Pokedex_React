from __future__ import annotations

import httpx
import pytest

from scripts.seed_from_pokeapi import (
    PokeApiClient,
    collect_catalog,
    collect_listing,
    evolution_edges,
    flavor_texts,
)


def test_flavor_texts_normalizes_and_keeps_languages() -> None:
    entries = [
        {"language": {"name": "en"}, "flavor_text": "A\nsmall\tmonster."},
        {"language": {"name": "en"}, "flavor_text": "duplicate"},
        {"language": {"name": "it"}, "flavor_text": "Un\nmostro."},
    ]
    assert flavor_texts(entries) == {"en": "A small monster.", "it": "Un mostro."}


def test_evolution_edges_flatten_chain() -> None:
    chain = {
        "chain": {
            "species": {"url": "https://pokeapi.co/api/v2/pokemon-species/1/"},
            "evolves_to": [
                {
                    "species": {"url": "https://pokeapi.co/api/v2/pokemon-species/2/"},
                    "evolution_details": [{"trigger": {"name": "level-up"}, "min_level": 16}],
                    "evolves_to": [],
                }
            ],
        }
    }
    assert evolution_edges(chain) == [
        {"from_species_id": 1, "to_species_id": 2, "trigger": "level-up", "min_level": 16}
    ]


@pytest.mark.asyncio
async def test_client_retries_transient_http_error() -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls < 3:
            return httpx.Response(503, request=request)
        return httpx.Response(200, json={"ok": True}, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        api = PokeApiClient(client, retries=2)
        assert await api.get("health") == {"ok": True}
    assert calls == 3


@pytest.mark.asyncio
async def test_collect_listing_follows_next_and_honors_limit() -> None:
    class FakeApi:
        async def get(self, url: str) -> dict[str, object]:
            if url == "pokemon?limit=100000&offset=0":
                return {
                    "results": [{"name": "one", "url": "https://pokeapi.co/1"}],
                    "next": "https://pokeapi.co/api/v2/pokemon?offset=1",
                }
            return {"results": [{"name": "two", "url": "https://pokeapi.co/2"}], "next": None}

    api = FakeApi()
    assert await collect_listing(api, "pokemon?limit=100000&offset=0") == [
        {"name": "one", "url": "https://pokeapi.co/1"},
        {"name": "two", "url": "https://pokeapi.co/2"},
    ]
    assert await collect_listing(api, "pokemon?limit=100000&offset=0", limit=1) == [
        {"name": "one", "url": "https://pokeapi.co/1"}
    ]


@pytest.mark.asyncio
async def test_collect_catalog_uses_pokemon_species_endpoint() -> None:
    class FakeApi:
        def __init__(self) -> None:
            self.urls: list[str] = []

        async def get(self, url: str) -> dict[str, object]:
            self.urls.append(url)
            if url == "pokemon?limit=100000&offset=0":
                return {
                    "results": [{"name": "one", "url": "pokemon/1"}],
                    "next": None,
                }
            if url == "pokemon/1":
                return {
                    "id": 1,
                    "name": "one",
                    "species": {"url": "pokemon-species/1"},
                    "stats": [],
                    "types": [],
                    "abilities": [],
                    "moves": [],
                }
            if url == "pokemon-species/1":
                return {
                    "id": 1,
                    "flavor_text_entries": [],
                    "generation": None,
                    "is_legendary": False,
                    "evolution_chain": None,
                }
            if url == "type?limit=100&offset=0":
                return {"results": [], "next": None}
            if url == "ability?limit=100000&offset=0":
                return {
                    "results": [
                        {"name": "unreferenced", "url": "ability/999"},
                    ],
                    "next": None,
                }
            if url == "move?limit=100000&offset=0":
                return {
                    "results": [
                        {"name": "unreferenced-move", "url": "move/999"},
                    ],
                    "next": None,
                }
            raise AssertionError(f"unexpected URL: {url}")

    api = FakeApi()
    catalog = await collect_catalog(api, limit=1)
    assert catalog["pokemon"][0]["name"] == "one"
    assert catalog["abilities"] == [{"id": 999, "name": "unreferenced"}]
    assert catalog["moves"] == [{"id": 999, "name": "unreferenced-move"}]
    assert "pokemon-species/1" in api.urls
    assert "species/1" not in api.urls


@pytest.mark.asyncio
async def test_collect_catalog_uses_authoritative_ability_and_move_listings() -> None:
    class FakeApi:
        async def get(self, url: str) -> dict[str, object]:
            if url == "ability?limit=100000&offset=0":
                return {
                    "results": [{"name": "hidden", "url": "ability/1"}],
                    "next": "ability?offset=1",
                }
            if url == "ability?offset=1":
                return {"results": [{"name": "unreferenced", "url": "ability/2"}], "next": None}
            if url == "move?limit=100000&offset=0":
                return {"results": [{"name": "move-a", "url": "move/1"}], "next": None}
            if url == "pokemon?limit=100000&offset=0":
                return {"results": [], "next": None}
            if url == "type?limit=100&offset=0":
                return {"results": [], "next": None}
            raise AssertionError(f"unexpected URL: {url}")

    catalog = await collect_catalog(FakeApi())
    assert catalog["abilities"] == [
        {"id": 1, "name": "hidden"},
        {"id": 2, "name": "unreferenced"},
    ]
    assert catalog["moves"] == [{"id": 1, "name": "move-a"}]
