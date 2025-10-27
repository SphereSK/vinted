"""Redis utilities for coordinating frontend/backend interactions."""
from __future__ import annotations

import json
import os
import socket
from datetime import datetime, timezone
from typing import Any, Optional

from dotenv import load_dotenv, find_dotenv

try:
    from redis.asyncio import Redis
    from redis.exceptions import RedisError
except ModuleNotFoundError:  # pragma: no cover - used during lightweight tests
    Redis = None  # type: ignore

load_dotenv(find_dotenv())

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_host_label = socket.gethostname().split(".")[0] if socket.gethostname() else "host"
REDIS_CLIENT_NAME = os.getenv(
    "REDIS_CLIENT_NAME",
    f"client_vinted_fastapi_{_host_label}_{os.getpid()}",
)

_redis_client: Optional["Redis"] = None
DETAIL_STATUS_KEY = "detail_status"
DETAIL_STATUS_CHANNEL = "detail_status"


def get_redis() -> Optional["Redis"]:
    """Return a shared Redis client instance."""
    global _redis_client
    if Redis is None:
        return None

    if _redis_client is None:
        _redis_client = Redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            client_name=REDIS_CLIENT_NAME,
        )
    return _redis_client


async def set_config_status(
    config_id: int,
    status: str,
    message: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Store runtime status for a scrape configuration."""
    payload: dict[str, Any] = {
        "config_id": str(config_id),
        "status": status,
        "message": message or "",
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    if extra:
        for key, value in extra.items():
            payload[key] = json.dumps(value) if isinstance(value, (dict, list)) else str(value)

    try:
        client = get_redis()
        if client is None:
            return payload
        await client.hset(f"config_status:{config_id}", mapping=payload)
        await client.publish("config_status", json.dumps(payload))
    except (RedisError, AttributeError):
        # Redis is optional; swallow errors to avoid breaking primary flow.
        pass

    return payload


async def get_config_status(config_id: int) -> Optional[dict[str, Any]]:
    """Fetch the runtime status for a scrape configuration."""
    try:
        client = get_redis()
        if client is None:
            return None
        data = await client.hgetall(f"config_status:{config_id}")
    except (RedisError, AttributeError):
        return None

    if not data:
        return None

    parsed: dict[str, Any] = {}
    for key, value in data.items():
        if key == "config_id":
            try:
                parsed[key] = int(value)
            except (TypeError, ValueError):
                parsed[key] = value
            continue
        if key in {"updated_at", "status", "message"}:
            parsed[key] = value
            continue
        try:
            parsed[key] = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            parsed[key] = value

    return parsed


async def set_detail_status(
    status: str,
    message: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Store runtime status for the detail scraping worker."""
    payload: dict[str, Any] = {
        "status": status,
        "message": message or "",
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    if extra:
        for key, value in extra.items():
            payload[key] = json.dumps(value) if isinstance(value, (dict, list)) else str(value)

    try:
        client = get_redis()
        if client is None:
            return payload
        await client.hset(DETAIL_STATUS_KEY, mapping=payload)
        await client.publish(DETAIL_STATUS_CHANNEL, json.dumps(payload))
    except (RedisError, AttributeError):
        pass

    return payload


async def get_detail_status() -> Optional[dict[str, Any]]:
    """Fetch the latest runtime status for the detail scraping worker."""
    try:
        client = get_redis()
        if client is None:
            return None
        data = await client.hgetall(DETAIL_STATUS_KEY)
    except (RedisError, AttributeError):
        return None

    if not data:
        return None

    parsed: dict[str, Any] = {}
    for key, value in data.items():
        if key in {"status", "message", "updated_at"}:
            parsed[key] = value
            continue
        try:
            parsed[key] = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            parsed[key] = value

    return parsed
