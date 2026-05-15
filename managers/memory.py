"""Memory management utilities.

Provides an in-memory manager for user conversation turns and simple
metadata, plus integration hooks for persisting into CocoIndex / SQLite.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Iterable

import cocoindex as coco
from cocoindex.connectors import sqlite as coco_sqlite

from core.config import cfg

BASE_DIR = Path(cfg.BASE_DIR)
STATE_PATH = BASE_DIR / "data" / "memory_state.json"
SQLITE_PATH = BASE_DIR / "data" / "memory.sqlite"
COCOINDEX_DB_PATH = BASE_DIR / "data" / "cocoindex_memory.db"

MEMORY_STORE_KEY = coco.ContextKey["MemoryManager"]("evilgpt_memory_store")
MEMORY_DB_KEY = coco.ContextKey[coco_sqlite.ManagedConnection]("evilgpt_memory_db")

_ACTIVE_MEMORY_MANAGER: "MemoryManager | None" = None


@dataclass(slots=True)
class MemoryTurn:
    """A single conversation turn between a user and the assistant.

    Attributes
    ----------
    turn_id : str
        Unique identifier for the turn.
    user_id : int
        Discord user id who sent the message.
    user_name : str
        Display name of the user.
    guild_id : int | None
        Guild id where the turn happened, or None for DMs.
    channel_id : int | None
        Channel id where the turn happened, or None for DMs.
    user_content : str
        The user message content.
    assistant_content : str | None
        The assistant's response content, may be None.
    created_at : float
        Timestamp when the turn was created.
    updated_at : float
        Timestamp when the turn was last updated.
    """

    turn_id: str
    user_id: int
    user_name: str
    guild_id: int | None
    channel_id: int | None
    user_content: str
    assistant_content: str | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass(slots=True)
class UserMetadataRecord:
    """Simple per-user metadata stored alongside turns.

    Attributes
    ----------
    user_id : int
        Discord user id this record belongs to.
    mood : str
        User mood preset used by the bot when replying.
    updated_at : float
        Timestamp of last update.
    """

    user_id: int
    mood: str = "sarcastic"
    updated_at: float = field(default_factory=time.time)


def _ensure_parent_dir(path: Path) -> None:
    """Ensure the parent directory of `path` exists.

    Parameters
    ----------
    path : Path
        File path whose parent directory should be created.
    """
    path.parent.mkdir(parents=True, exist_ok=True)


@coco.lifespan
async def memory_lifespan(builder: coco.EnvironmentBuilder) -> AsyncIterator[None]:
    """CocoIndex lifespan hook to provide memory-related services.

    The active MemoryManager and a managed SQLite connection are provided
    into the CocoIndex environment during the application's lifespan.

    Parameters
    ----------
    builder : coco.EnvironmentBuilder
        CocoIndex environment builder used to register providers.

    Raises
    ------
    RuntimeError
        If the MemoryManager singleton has not been initialized.
    """
    manager = _ACTIVE_MEMORY_MANAGER
    if manager is None:
        raise RuntimeError("MemoryManager is not initialized.")

    builder.settings.db_path = manager.cocoindex_db_path

    with coco_sqlite.managed_connection(manager.sqlite_path, load_vec=False) as conn:
        builder.provide(MEMORY_STORE_KEY, manager)
        builder.provide(MEMORY_DB_KEY, conn)
        yield


@coco.fn
async def memory_app_main() -> None:
    """CocoIndex function to declare DB tables from in-memory records.

    This function is used by the CocoIndex app to prepare table schemas and
    declare rows based on the in-memory store.
    """
    store = coco.use_context(MEMORY_STORE_KEY)

    turn_schema = await coco_sqlite.TableSchema.from_class(
        MemoryTurn, primary_key=["turn_id"]
    )
    metadata_schema = await coco_sqlite.TableSchema.from_class(
        UserMetadataRecord, primary_key=["user_id"]
    )

    turn_table = await coco_sqlite.mount_table_target(
        MEMORY_DB_KEY,
        "memory_turns",
        turn_schema,
    )
    metadata_table = await coco_sqlite.mount_table_target(
        MEMORY_DB_KEY,
        "memory_metadata",
        metadata_schema,
    )

    for turn in store.iter_turns():
        turn_table.declare_row(row=turn)

    for record in store.iter_metadata_records():
        metadata_table.declare_row(row=record)


class MemoryManager:
    """In-memory conversation history manager with persistence hooks.

    The manager stores recent `MemoryTurn` objects and simple per-user
    metadata, supports recording/deleting turns and syncing to disk /
    CocoIndex-backed storage.
    """

    def __init__(
        self,
        max_history: int = 15,
        *,
        state_path: Path | str = STATE_PATH,
        sqlite_path: Path | str = SQLITE_PATH,
        cocoindex_db_path: Path | str = COCOINDEX_DB_PATH,
    ) -> None:
        """_summary_.

        Parameters
        ----------
        max_history : int
            _description_ (Default value = 15)
        state_path : Path | str
            _description_ (Default value = STATE_PATH)
        sqlite_path : Path | str
            _description_ (Default value = SQLITE_PATH)
        cocoindex_db_path : Path | str
            _description_ (Default value = COCOINDEX_DB_PATH)
        """
        global _ACTIVE_MEMORY_MANAGER

        _ACTIVE_MEMORY_MANAGER = self
        self.max_history = max_history
        self.state_path = Path(state_path)
        self.sqlite_path = Path(sqlite_path)
        self.cocoindex_db_path = Path(cocoindex_db_path)
        self._turns: dict[str, MemoryTurn] = {}
        self._metadata: dict[int, UserMetadataRecord] = {}
        self._sync_lock = asyncio.Lock()
        self._app = coco.App(coco.AppConfig(name="EvilGPTMemory"), memory_app_main)

        _ensure_parent_dir(self.state_path)
        _ensure_parent_dir(self.sqlite_path)
        _ensure_parent_dir(self.cocoindex_db_path)
        self._load_state()

    def _load_state(self) -> None:
        """_summary_."""
        if not self.state_path.exists():
            return

        try:
            with self.state_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except Exception:
            return

        turns = payload.get("turns", []) if isinstance(payload, dict) else []
        metadata = payload.get("metadata", []) if isinstance(payload, dict) else []

        for item in turns:
            try:
                turn = MemoryTurn(**item)
            except Exception:
                continue
            self._turns[turn.turn_id] = turn

        for item in metadata:
            try:
                record = UserMetadataRecord(**item)
            except Exception:
                continue
            self._metadata[record.user_id] = record

    def _save_state(self) -> None:
        """_summary_."""
        payload = {
            "turns": [asdict(turn) for turn in self.iter_turns()],
            "metadata": [asdict(record) for record in self.iter_metadata_records()],
        }
        tmp_path = self.state_path.with_suffix(".json.tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=True, indent=2)
        tmp_path.replace(self.state_path)

    def _sorted_turns(self) -> list[MemoryTurn]:
        """_summary_.

        Returns
        -------
        list[MemoryTurn]
            _description_
        """
        return sorted(
            self._turns.values(), key=lambda turn: (turn.created_at, turn.turn_id)
        )

    def iter_turns(self) -> Iterable[MemoryTurn]:
        """_summary_.

        Returns
        -------
        Iterable[MemoryTurn]
            _description_
        """
        return self._sorted_turns()

    def iter_metadata_records(self) -> Iterable[UserMetadataRecord]:
        """_summary_.

        Returns
        -------
        Iterable[UserMetadataRecord]
            _description_
        """
        return sorted(self._metadata.values(), key=lambda record: record.user_id)

    def _resolve_turn_id(self, turn_id: str) -> str:
        """_summary_.

        Parameters
        ----------
        turn_id : str
            _description_

        Returns
        -------
        str
            _description_

        Raises
        ------
        KeyError
            _description_
        ValueError
            _description_
        """
        if turn_id in self._turns:
            return turn_id

        matches = [
            existing_id
            for existing_id in self._turns
            if existing_id.startswith(turn_id)
        ]
        if not matches:
            raise KeyError(turn_id)
        if len(matches) > 1:
            raise ValueError(f"Turn ID '{turn_id}' is ambiguous.")
        return matches[0]

    def get_metadata(self, user_id: int, key: str | None = None) -> Any:
        """_summary_.

        Parameters
        ----------
        user_id : int
            _description_
        key : str | None
            _description_ (Default value = None)

        Returns
        -------
        Any
            _description_
        """
        record = self._metadata.get(user_id)
        if key is None:
            return {"mood": record.mood if record else "sarcastic"}
        if record is None:
            if key == "mood":
                return "sarcastic"
            return None
        return getattr(record, key, None)

    def set_metadata(self, user_id: int, key: str, value: Any) -> None:
        """_summary_.

        Parameters
        ----------
        user_id : int
            _description_
        key : str
            _description_
        value : Any
            _description_

        Raises
        ------
        ValueError
            _description_
        """
        if key != "mood":
            raise ValueError(f"Unsupported metadata key: {key}")
        record = self._metadata.get(user_id)
        if record is None:
            record = UserMetadataRecord(user_id=user_id)
            self._metadata[user_id] = record
        record.mood = str(value)
        record.updated_at = time.time()

    def get_turn(self, turn_id: str) -> MemoryTurn:
        """_summary_.

        Parameters
        ----------
        turn_id : str
            _description_

        Returns
        -------
        MemoryTurn
            _description_
        """
        return self._turns[self._resolve_turn_id(turn_id)]

    def list_turns(
        self, user_id: int | None = None, limit: int = 10
    ) -> list[MemoryTurn]:
        """_summary_.

        Parameters
        ----------
        user_id : int | None
            _description_ (Default value = None)
        limit : int
            _description_ (Default value = 10)

        Returns
        -------
        list[MemoryTurn]
            _description_
        """
        turns = list(self.iter_turns())
        if user_id is not None:
            turns = [turn for turn in turns if turn.user_id == user_id]
        return turns[-max(0, limit) :]

    def get_history(
        self, user_id: int, limit: int | None = None
    ) -> list[dict[str, str]]:
        """_summary_.

        Parameters
        ----------
        user_id : int
            _description_
        limit : int | None
            _description_ (Default value = None)

        Returns
        -------
        list[dict[str, str]]
            _description_
        """
        turns = [turn for turn in self.iter_turns() if turn.user_id == user_id]
        if limit is not None:
            turns = turns[-max(0, limit) :]

        messages: list[dict[str, str]] = []
        for turn in turns:
            messages.append({"role": "user", "content": turn.user_content})
            if turn.assistant_content:
                messages.append(
                    {"role": "assistant", "content": turn.assistant_content}
                )
        return messages

    def record_exchange(
        self,
        *,
        user_id: int,
        user_name: str,
        user_content: str,
        assistant_content: str,
        guild_id: int | None,
        channel_id: int | None,
        turn_id: str | None = None,
    ) -> str:
        """_summary_.

        Parameters
        ----------
        user_id : int
            _description_
        user_name : str
            _description_
        user_content : str
            _description_
        assistant_content : str
            _description_
        guild_id : int | None
            _description_
        channel_id : int | None
            _description_
        turn_id : str | None
            _description_ (Default value = None)

        Returns
        -------
        str
            _description_
        """
        turn = MemoryTurn(
            turn_id=turn_id or uuid.uuid4().hex,
            user_id=user_id,
            user_name=user_name,
            guild_id=guild_id,
            channel_id=channel_id,
            user_content=user_content,
            assistant_content=assistant_content,
        )
        self._turns[turn.turn_id] = turn
        return turn.turn_id

    def delete_turn(self, turn_id: str) -> MemoryTurn:
        """_summary_.

        Parameters
        ----------
        turn_id : str
            _description_

        Returns
        -------
        MemoryTurn
            _description_
        """
        resolved = self._resolve_turn_id(turn_id)
        return self._turns.pop(resolved)

    def clear_history(self, user_id: int | None = None) -> int:
        """_summary_.

        Parameters
        ----------
        user_id : int | None
            _description_ (Default value = None)

        Returns
        -------
        int
            _description_
        """
        if user_id is None:
            removed = len(self._turns)
            self._turns.clear()
            return removed

        removed_turn_ids = [
            turn_id for turn_id, turn in self._turns.items() if turn.user_id == user_id
        ]
        for turn_id in removed_turn_ids:
            self._turns.pop(turn_id, None)
        return len(removed_turn_ids)

    async def sync(self) -> None:
        """_summary_."""
        async with self._sync_lock:
            self._save_state()
            await self._app.update()

    async def bootstrap(self) -> None:
        """_summary_."""
        await self.sync()

    async def record_and_sync(
        self,
        *,
        user_id: int,
        user_name: str,
        user_content: str,
        assistant_content: str,
        guild_id: int | None,
        channel_id: int | None,
    ) -> str:
        """_summary_.

        Parameters
        ----------
        user_id : int
            _description_
        user_name : str
            _description_
        user_content : str
            _description_
        assistant_content : str
            _description_
        guild_id : int | None
            _description_
        channel_id : int | None
            _description_

        Returns
        -------
        str
            _description_
        """
        async with self._sync_lock:
            turn_id = self.record_exchange(
                user_id=user_id,
                user_name=user_name,
                user_content=user_content,
                assistant_content=assistant_content,
                guild_id=guild_id,
                channel_id=channel_id,
            )
            self._save_state()
            await self._app.update()
            return turn_id

    async def set_metadata_and_sync(self, user_id: int, key: str, value: Any) -> None:
        """_summary_.

        Parameters
        ----------
        user_id : int
            _description_
        key : str
            _description_
        value : Any
            _description_
        """
        async with self._sync_lock:
            self.set_metadata(user_id, key, value)
            self._save_state()
            await self._app.update()

    async def delete_turn_and_sync(self, turn_id: str) -> MemoryTurn:
        """_summary_.

        Parameters
        ----------
        turn_id : str
            _description_

        Returns
        -------
        MemoryTurn
            _description_
        """
        async with self._sync_lock:
            turn = self.delete_turn(turn_id)
            self._save_state()
            await self._app.update()
            return turn

    async def clear_history_and_sync(self, user_id: int | None = None) -> int:
        """_summary_.

        Parameters
        ----------
        user_id : int | None
            _description_ (Default value = None)

        Returns
        -------
        int
            _description_
        """
        async with self._sync_lock:
            removed = self.clear_history(user_id)
            self._save_state()
            await self._app.update()
            return removed
