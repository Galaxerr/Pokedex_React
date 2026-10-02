"""Populate the catalog from PokéAPI in one repeatable transaction."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, cast

import httpx
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Support both `python scripts/seed_from_pokeapi.py` and module imports from backend.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.models import (  # noqa: E402
    Ability,
    Evolution,
    Move,
    Pokemon,
    PokemonAbility,
    PokemonMove,
    PokemonStat,
    PokemonType,
    Species,
    Type,
    TypeRelation,
)

LOGGER = logging.getLogger("pokedex.seed")
DEFAULT_BASE_URL = "https://pokeapi.co/api/v2"
DEFAULT_TIMEOUT = 30.0
DEFAULT_RETRIES = 3


def resource_id(resource: dict[str, Any]) -> int:
    """Extract the numeric API id from a list/detail resource."""
    return int(str(resource["url"]).rstrip("/").split("/")[-1])


def flavor_texts(entries: list[dict[str, Any]]) -> dict[str, str]:
    """Keep one cleaned flavor text per available language."""
    values: dict[str, str] = {}
    for entry in entries:
        language = entry.get("language", {}).get("name")
        text = " ".join(str(entry.get("flavor_text", "")).split())
        if language and text and language not in values:
            values[language] = text
    return values


def evolution_edges(chain: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten a PokéAPI evolution chain into database-ready directed edges."""
    edges: list[dict[str, Any]] = []

    def walk(node: dict[str, Any]) -> None:
        source_id = resource_id(node["species"])
        for link in node.get("evolves_to", []):
            detail = (link.get("evolution_details") or [{}])[0]
            edges.append(
                {
                    "from_species_id": source_id,
                    "to_species_id": resource_id(link["species"]),
                    "trigger": (detail.get("trigger") or {}).get("name"),
                    "min_level": detail.get("min_level"),
                }
            )
            walk(link)

    walk(chain["chain"])
    return edges


class PokeApiClient:
    """Retrying client with optional JSON-on-disk cache for resumable downloads."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        base_url: str = DEFAULT_BASE_URL,
        retries: int = DEFAULT_RETRIES,
        cache_dir: Path | None = None,
    ) -> None:
        self.client = client
        self.base_url = base_url.rstrip("/")
        self.retries = retries
        self.cache_dir = cache_dir

    async def get(self, url: str) -> dict[str, Any]:
        absolute = url if url.startswith("http") else f"{self.base_url}/{url.lstrip('/')}"
        cache_file = self._cache_file(absolute)
        if cache_file and cache_file.exists():
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            if not isinstance(cached, dict):
                raise RuntimeError(f"Unexpected non-object cache response from {absolute}")
            return cast(dict[str, Any], cached)
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = await self.client.get(absolute)
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise RuntimeError(f"Unexpected non-object response from {absolute}")
                if cache_file:
                    cache_file.parent.mkdir(parents=True, exist_ok=True)
                    cache_file.write_text(json.dumps(payload), encoding="utf-8")
                return cast(dict[str, Any], payload)
            except (httpx.HTTPError, RuntimeError) as exc:
                last_error = exc
                if attempt < self.retries:
                    await asyncio.sleep(0.5 * (2**attempt))
        raise RuntimeError(
            f"PokéAPI request failed after {self.retries + 1} attempts: {absolute}"
        ) from last_error

    def _cache_file(self, url: str) -> Path | None:
        if self.cache_dir is None:
            return None
        safe_name = url.replace(self.base_url, "").strip("/").replace("/", "_")
        return self.cache_dir / f"{safe_name or 'root'}.json"


async def collect_catalog(
    api: PokeApiClient, limit: int | None = None
) -> dict[str, list[dict[str, Any]]]:
    """Download and normalize all seed-owned resources before touching PostgreSQL."""
    refs = await collect_listing(api, "pokemon?limit=100000&offset=0", limit=limit)
    details = [await api.get(item["url"]) for item in refs]
    species_ids = sorted({resource_id(item["species"]) for item in details})
    species_details = {
        item_id: await api.get(f"pokemon-species/{item_id}") for item_id in species_ids
    }

    type_refs = await collect_listing(api, "type?limit=100&offset=0")
    type_ids = sorted({resource_id(item) for item in type_refs})
    type_details = [await api.get(f"type/{item_id}") for item_id in type_ids]
    types = [{"id": item["id"], "name": item["name"], "color": None} for item in type_details]
    type_relations: list[dict[str, Any]] = []
    for item in type_details:
        for relation_name, multiplier in (
            ("double_damage_to", 2.0),
            ("half_damage_to", 0.5),
            ("no_damage_to", 0.0),
        ):
            for target in item["damage_relations"].get(relation_name, []):
                type_relations.append(
                    {
                        "attacker_type": item["id"],
                        "defender_type": resource_id(target),
                        "multiplier": multiplier,
                    }
                )

    # The Pokémon detail payload only contains resources referenced by a
    # Pokémon.  That omits valid catalogue entries such as ``struggle`` and
    # ``happy-hour``.  Load the authoritative paginated listings separately,
    # then let Pokémon payloads contribute association rows below.
    ability_refs = await collect_listing(api, "ability?limit=100000&offset=0")
    move_refs = await collect_listing(api, "move?limit=100000&offset=0")
    abilities = {
        resource_id(item): {"id": resource_id(item), "name": item["name"]} for item in ability_refs
    }
    moves = {
        resource_id(item): {"id": resource_id(item), "name": item["name"]} for item in move_refs
    }

    pokemon: list[dict[str, Any]] = []
    stats: list[dict[str, Any]] = []
    pokemon_types: list[dict[str, Any]] = []
    pokemon_abilities: list[dict[str, Any]] = []
    pokemon_moves: list[dict[str, Any]] = []
    for item in details:
        sprites = item.get("sprites") or {}
        artwork = (sprites.get("other") or {}).get("official-artwork") or {}
        pokemon.append(
            {
                "id": item["id"],
                "name": item["name"],
                "height": item.get("height"),
                "weight": item.get("weight"),
                "base_experience": item.get("base_experience"),
                "sprite_url": sprites.get("front_default"),
                "artwork_url": artwork.get("front_default"),
                "species_id": resource_id(item["species"]),
            }
        )
        stats.extend(
            {
                "pokemon_id": item["id"],
                "stat_name": stat["stat"]["name"],
                "base_value": stat["base_stat"],
            }
            for stat in item.get("stats", [])
        )
        pokemon_types.extend(
            {
                "pokemon_id": item["id"],
                "type_id": resource_id(value["type"]),
                "slot": value.get("slot"),
            }
            for value in item.get("types", [])
        )
        for value in item.get("abilities", []):
            ability_id = resource_id(value["ability"])
            abilities[ability_id] = {"id": ability_id, "name": value["ability"]["name"]}
            pokemon_abilities.append(
                {
                    "pokemon_id": item["id"],
                    "ability_id": ability_id,
                    "is_hidden": value["is_hidden"],
                }
            )
        for value in item.get("moves", []):
            move_id = resource_id(value["move"])
            moves[move_id] = {"id": move_id, "name": value["move"]["name"]}
            for version in value.get("version_group_details", []):
                pokemon_moves.append(
                    {
                        "pokemon_id": item["id"],
                        "move_id": move_id,
                        "version_group": (version.get("version_group") or {}).get("name"),
                        "level": version.get("level_learned_at"),
                        "method": (version.get("move_learn_method") or {}).get("name"),
                    }
                )

    species: list[dict[str, Any]] = []
    evolutions: list[dict[str, Any]] = []
    seen_chains: set[str] = set()
    for item in species_details.values():
        generation_url = (item.get("generation") or {}).get("url")
        species.append(
            {
                "id": item["id"],
                "flavor_text": flavor_texts(item.get("flavor_text_entries", [])),
                "generation": int(generation_url.rstrip("/").split("/")[-1])
                if generation_url
                else None,
                "is_legendary": item.get("is_legendary"),
                "evolution_chain_id": resource_id(item["evolution_chain"])
                if item.get("evolution_chain")
                else None,
            }
        )
        chain_url = (item.get("evolution_chain") or {}).get("url")
        if chain_url and chain_url not in seen_chains:
            seen_chains.add(chain_url)
            evolutions.extend(evolution_edges(await api.get(chain_url)))

    return {
        "pokemon": pokemon,
        "stats": stats,
        "types": types,
        "pokemon_types": pokemon_types,
        "type_relations": type_relations,
        "abilities": list(abilities.values()),
        "pokemon_abilities": pokemon_abilities,
        "moves": list(moves.values()),
        "pokemon_moves": pokemon_moves,
        "species": species,
        "evolutions": evolutions,
    }


async def collect_listing(
    api: PokeApiClient, path: str, *, limit: int | None = None
) -> list[dict[str, Any]]:
    """Collect all pages from a PokéAPI list endpoint, optionally capped."""
    results: list[dict[str, Any]] = []
    next_url: str | None = path
    while next_url:
        page = await api.get(next_url)
        page_results = page.get("results", [])
        if not isinstance(page_results, list):
            raise RuntimeError(f"Unexpected results payload from {next_url}")
        results.extend(cast(list[dict[str, Any]], page_results))
        if limit is not None and len(results) >= limit:
            return results[:limit]
        next_value = page.get("next")
        next_url = str(next_value) if next_value else None
    return results


async def replace_catalog(session: AsyncSession, catalog: dict[str, list[dict[str, Any]]]) -> None:
    """Replace all seed-owned rows in FK-safe order inside the caller's transaction."""
    for model in (
        PokemonMove,
        PokemonAbility,
        PokemonType,
        PokemonStat,
        Evolution,
        Pokemon,
        Move,
        Ability,
        TypeRelation,
        Type,
        Species,
    ):
        await session.execute(delete(model))
    models: dict[str, type[Any]] = {
        "species": Species,
        "types": Type,
        "abilities": Ability,
        "moves": Move,
        "pokemon": Pokemon,
        "stats": PokemonStat,
        "pokemon_types": PokemonType,
        "type_relations": TypeRelation,
        "pokemon_abilities": PokemonAbility,
        "pokemon_moves": PokemonMove,
        "evolutions": Evolution,
    }
    for key, model in models.items():
        if catalog[key]:
            session.add_all([model(**row) for row in catalog[key]])
    await session.flush()


async def seed(
    database_url: str, *, limit: int | None = None, cache_dir: Path | None = None
) -> dict[str, int]:
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(DEFAULT_TIMEOUT), headers={"User-Agent": "pokedex-seed/1.0"}
    ) as client:
        catalog = await collect_catalog(PokeApiClient(client, cache_dir=cache_dir), limit=limit)
    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory.begin() as session:
            await replace_catalog(session, catalog)
        return {key: len(value) for key, value in catalog.items()}
    finally:
        await engine.dispose()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit", type=int, help="Only seed the first N Pokémon (verification helper)."
    )
    parser.add_argument("--cache-dir", type=Path, help="Optional ignored JSON cache for downloads.")
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL"),
        help="Async PostgreSQL URL (defaults to DATABASE_URL).",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()
    if not args.database_url:
        raise SystemExit("DATABASE_URL is required (postgresql+asyncpg://...)")
    counts = asyncio.run(seed(args.database_url, limit=args.limit, cache_dir=args.cache_dir))
    LOGGER.info("Seed completed atomically: %s", counts)


if __name__ == "__main__":
    main()
