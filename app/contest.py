from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Dict

from . import config
from .storage import load_json, save_json


@dataclass
class ContestStatus:
    active: bool
    start_ts: float
    end_ts: float
    top_score: int
    top_name: str
    last_score: int
    last_name: str
    scores: List[Dict[str, int | str]]


class ContestManager:
    def __init__(self, data_path: str) -> None:
        self._path = data_path
        self._data = load_json(self._path, {})
        self._normalize()

    def _normalize(self) -> None:
        now = time.time()
        active = bool(self._data.get("active"))
        start_ts = float(self._data.get("start_ts", 0.0))
        end_ts = float(self._data.get("end_ts", 0.0))
        top_score = int(self._data.get("top_score", 0))
        top_name = str(self._data.get("top_name", "---"))
        last_score = int(self._data.get("last_score", 0))
        last_name = str(self._data.get("last_name", "---"))
        scores = list(self._data.get("scores", []))

        if active and end_ts <= now:
            active = False

        scores = self._normalize_scores(scores, top_score, top_name)
        if scores:
            top_score = int(scores[0]["score"])
            top_name = str(scores[0]["name"])
        else:
            top_score = 0
            top_name = "---"

        self._data = {
            "active": active,
            "start_ts": start_ts,
            "end_ts": end_ts,
            "top_score": top_score,
            "top_name": top_name,
            "last_score": last_score,
            "last_name": last_name,
            "scores": scores,
        }

    def _persist(self) -> None:
        save_json(self._path, self._data)

    def _normalize_scores(self, scores, top_score: int, top_name: str):
        normalized = []
        for entry in scores:
            try:
                name = str(entry.get("name", "---"))[:3]
                score = int(entry.get("score", 0))
            except Exception:
                continue
            if score <= 0:
                continue
            normalized.append({"name": name, "score": score})

        if not normalized and top_score > 0:
            normalized.append({"name": top_name[:3], "score": top_score})

        normalized.sort(key=lambda item: int(item["score"]), reverse=True)
        return normalized[:5]

    def ensure_active(self) -> None:
        now = time.time()
        if not self._data["active"]:
            self._data["active"] = True
            self._data["start_ts"] = now
            self._data["end_ts"] = now + config.CONTEST_DURATION_SEC
            self._data["top_score"] = 0
            self._data["top_name"] = "---"
            self._data["last_score"] = 0
            self._data["last_name"] = "---"
            self._data["scores"] = []
            self._persist()

    def register_score(self, score: int, name: str) -> None:
        now = time.time()
        if not self._data["active"] or now >= self._data["end_ts"]:
            self._data["active"] = True
            self._data["start_ts"] = now
            self._data["end_ts"] = now + config.CONTEST_DURATION_SEC
            self._data["top_score"] = 0
            self._data["top_name"] = "---"
            self._data["scores"] = []

        self._data["last_score"] = int(score)
        self._data["last_name"] = name
        scores = list(self._data.get("scores", []))
        scores.append({"name": name, "score": int(score)})
        scores = self._normalize_scores(scores, self._data["top_score"], self._data["top_name"])
        self._data["scores"] = scores
        if scores:
            self._data["top_score"] = int(scores[0]["score"])
            self._data["top_name"] = str(scores[0]["name"])

        self._persist()

    def time_left(self) -> float:
        if not self._data["active"]:
            return 0.0
        return max(0.0, self._data["end_ts"] - time.time())

    def status(self) -> ContestStatus:
        self._normalize()
        return ContestStatus(
            active=self._data["active"],
            start_ts=self._data["start_ts"],
            end_ts=self._data["end_ts"],
            top_score=self._data["top_score"],
            top_name=self._data["top_name"],
            last_score=self._data["last_score"],
            last_name=self._data["last_name"],
            scores=list(self._data.get("scores", [])),
        )
