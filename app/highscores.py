from dataclasses import dataclass
from typing import Dict, List

from .storage import load_json, save_json


@dataclass
class ScoreStatus:
    scores: List[Dict[str, int | str]]
    top_score: int
    top_name: str
    last_score: int
    last_name: str


class HighScoreManager:
    def __init__(self, data_path: str) -> None:
        self._path = data_path
        self._data = load_json(self._path, {})
        if "games" not in self._data:
            self._data = {"games": {}}

    def _persist(self) -> None:
        save_json(self._path, self._data)

    def _normalize_scores(self, scores):
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
        normalized.sort(key=lambda item: int(item["score"]), reverse=True)
        return normalized[:5]

    def get_status(self, game_id: str) -> ScoreStatus:
        game = self._data.get("games", {}).get(game_id, {})
        scores = self._normalize_scores(game.get("scores", []))
        top_score = int(scores[0]["score"]) if scores else 0
        top_name = str(scores[0]["name"]) if scores else "---"
        last_score = int(game.get("last_score", 0))
        last_name = str(game.get("last_name", "---"))
        return ScoreStatus(scores=scores, top_score=top_score, top_name=top_name,
                           last_score=last_score, last_name=last_name)

    def register_score(self, game_id: str, score: int, name: str) -> None:
        game = self._data.setdefault("games", {}).setdefault(game_id, {})
        scores = list(game.get("scores", []))
        scores.append({"name": name[:3], "score": int(score)})
        scores = self._normalize_scores(scores)
        game["scores"] = scores
        game["last_score"] = int(score)
        game["last_name"] = name[:3]
        self._persist()
