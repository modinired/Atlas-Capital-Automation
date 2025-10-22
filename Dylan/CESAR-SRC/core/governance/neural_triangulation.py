
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_BUNDLE_LOCATIONS: List[Path] = [
    Path(os.getenv("CESAR_CIA_BUNDLE_PATH", "")),
    Path.home()
    / "Library/Mobile Documents/com~apple~CloudDocs/cesar_cia_bundle_v1_2",
]


class MissingCIABundle(RuntimeError):
    """Raised when the CESAR CIA bundle cannot be located."""


@dataclass
class TriangulationVerdict:
    plan: Dict[str, Any]
    rationales: List[str]
    confidence_score: float
    governance: Dict[str, Any]


class NeuralTriangulationEngine:
    """Evaluates droid outputs against the CESAR CIA protocols.

    The engine loads the Triarch (reasoning) and Jules (governance) schemas from
    the CIA bundle and applies lightweight rules to generate a combined mission
    verdict. This provides a deterministic hook for neural triangulation: cross
    validating insights from research, execution, and communications agents,
    while emitting governance guidance.
    """

    def __init__(self, bundle_path: Optional[Path] = None) -> None:
        self.bundle_path = self._resolve_bundle(bundle_path)
        self.protocols = self._load_protocols()
        self.governance_policies = self._load_json("ops/governance_policies.json")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def evaluate(
        self,
        mission: str,
        droid_outputs: Dict[str, Any],
    ) -> TriangulationVerdict:
        """Compute the plan/rationale/confidence roll\u2011up for a mission."""
        plan_steps: List[Dict[str, Any]] = []
        rationales: List[str] = []
        confidence_values: List[float] = []
        governance_flags: List[str] = []

        for alias, output in droid_outputs.items():
            confidence = float(output.confidence or 0.0)
            confidence_values.append(confidence)
            plan_steps.append(
                {
                    "agent": alias,
                    "status": output.status.value,
                    "confidence": confidence,
                    "artifact_keys": sorted(list(output.result.keys())),
                }
            )

            rationale = self._derive_rationale(alias, confidence, output.result)
            rationales.append(rationale)

            if confidence < 0.6 or output.status.value != "success":
                governance_flags.append(
                    f"{alias} requires review \u2014 confidence {confidence:.2f}"
                )

        avg_confidence = sum(confidence_values) / max(len(confidence_values), 1)
        governance_summary = {
            "bundle": str(self.bundle_path),
            "protocols": list(self.protocols.keys()),
            "flags": governance_flags,
            "policies": {
                "jules_required": self.protocols["jules"]["governance"][
                    "jules_required"
                ],
                "audit": self.protocols["jules"]["governance"]["audit"],
            },
        }

        plan = {
            "protocol": self.protocols["triarch"]["name"],
            "mission": mission,
            "steps": plan_steps,
        }

        return TriangulationVerdict(
            plan=plan,
            rationales=rationales,
            confidence_score=avg_confidence,
            governance=governance_summary,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _resolve_bundle(self, explicit: Optional[Path]) -> Path:
        candidates = []
        if explicit:
            candidates.append(explicit.expanduser())
        for path in DEFAULT_BUNDLE_LOCATIONS:
            if path:
                candidates.append(path.expanduser())

        for candidate in candidates:
            if candidate and candidate.exists():
                return candidate
        raise MissingCIABundle(
            "CESAR CIA bundle not found. Set CESAR_CIA_BUNDLE_PATH or place "
            "cesar_cia_bundle_v1_2 in iCloud."  # noqa: E501
        )

    def _load_protocols(self) -> Dict[str, Dict[str, Any]]:
        protocols = {}
        for name in ("triarch", "jules", "aletheia", "kairos"):
            protocols[name] = self._load_json(f"protocol_schemas/{name}.json")
        return protocols

    def _load_json(self, relative_path: str) -> Dict[str, Any]:
        file_path = self.bundle_path / relative_path
        with file_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _derive_rationale(
        self,
        alias: str,
        confidence: float,
        result: Dict[str, Any],
    ) -> str:
        highlight = result.get("research_summary") or result.get(
            "automation_summary"
        ) or result.get("communications") or result.get("summary")

        if isinstance(highlight, list):
            highlight = highlight[0]
        if isinstance(highlight, dict):
            highlight = json.dumps(highlight, ensure_ascii=False)[:200]

        return (
            f"{alias} delivered with confidence {confidence:.2f}. "
            f"Highlight: {highlight if highlight else 'artifact recorded.'}"
        )


__all__ = ["NeuralTriangulationEngine", "TriangulationVerdict", "MissingCIABundle"]
