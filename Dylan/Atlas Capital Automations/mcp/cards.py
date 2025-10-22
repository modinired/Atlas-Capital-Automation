"""
Card definitions for the MCP orchestration engine.

Cards are declarative blueprints that define a high‑level task,
specify required inputs, list the plan steps (tools and arguments),
establish evidence contracts and output artefacts.  This module
contains two example cards inspired by the CESAR‑SRC patterns:

* ``QBR`` – Quarterly Business Review preparation.  Retrieves KPI
  definitions, summarises performance using multiple models, adjudicates
  results and enforces a no‑PII policy.
* ``IncidentPostmortem`` – Drafts an incident postmortem by fetching
  logs, summarising impact, validating against runbooks, adjudicating
  summaries and enforcing policy.

Cards can be executed via :func:`mcp.workflow.run_card`.  They
illustrate how to compose the primitives from ``mcp.knowledge``,
``mcp.triangulator`` and ``mcp.policy``.

Each card descriptor has the following top‑level keys:

* ``card`` – human‑readable name
* ``version`` – semantic version of the card definition
* ``inputs`` – specification of expected input fields
* ``plan`` – list of task objects to execute in order
* ``outputs`` – mapping of output filenames to context keys
* ``thresholds`` – optional acceptance thresholds for adjudication

See the file ``cards.yaml`` in the project root for future
extensibility.
"""

from __future__ import annotations

from typing import Any, Dict


CARDS: Dict[str, Dict[str, Any]] = {
    "QBR": {
        "card": "Quarterly Business Review",
        "version": "1.0.0",
        "inputs": {
            "accounts": list,
            "time_window": str,
            "kpi_definitions": dict,
            "file_locations": dict,
        },
        "plan": [
            {
                "tool": "knowledge.ground",
                "args": {
                    "query": "KPIs for ${accounts}",
                    "space": "kpi",
                    "k": 5,
                    "freshness": "${time_window}",
                },
                "save_as": "evidence",
            },
            {
                "tool": "triangulator.route",
                "args": {
                    "task": "summarise KPI performance",
                    "models": ["local_echo", "local_reverse"],
                    "latency_budget_ms": 5000,
                    "cost_ceiling": 1.0,
                },
                "save_as": "candidates",
            },
            {
                "tool": "triangulator.adjudicate",
                "args": {
                    "candidates": "${candidates}",
                    "rubric": [
                        {"name": "Non-empty", "weight": 0.6, "criteria": "Output must not be empty"},
                        {"name": "Shorter is better", "weight": 0.4, "criteria": "Concise summaries"},
                    ],
                },
                "save_as": "judgement",
            },
            {
                "tool": "policy.enforce",
                "args": {
                    "payload": "${judgement}",
                    "policy_id": "no_pii",
                },
                "save_as": "policy_result",
                "gate": {"on_fail": ["denied"]},
            },
        ],
        "outputs": {
            "judgement.json": "judgement",
            "policy.json": "policy_result",
            "evidence.json": "evidence",
        },
        "thresholds": {
            "score_min": 0.8,
        },
    },
    "IncidentPostmortem": {
        "card": "Incident Postmortem Draft",
        "version": "1.0.0",
        "inputs": {
            "incident_id": str,
            "log_paths": list,
            "time_range": str,
        },
        "plan": [
            {
                "tool": "knowledge.ground",
                "args": {
                    "query": "runbooks for ${incident_id}",
                    "space": "runbooks",
                    "k": 3,
                    "freshness": "${time_range}",
                },
                "save_as": "runbook_evidence",
            },
            {
                "tool": "triangulator.route",
                "args": {
                    "task": "summarise incident impact",
                    "models": ["local_echo", "local_reverse"],
                    "latency_budget_ms": 5000,
                    "cost_ceiling": 1.0,
                },
                "save_as": "candidates",
            },
            {
                "tool": "triangulator.adjudicate",
                "args": {
                    "candidates": "${candidates}",
                    "rubric": [
                        {"name": "Non-empty", "weight": 0.5, "criteria": "Must not be empty"},
                        {"name": "Shorter is better", "weight": 0.5, "criteria": "Concise"},
                    ],
                },
                "save_as": "judgement",
            },
            {
                "tool": "policy.enforce",
                "args": {
                    "payload": "${judgement}",
                    "policy_id": "no_pii",
                },
                "save_as": "policy_result",
                "gate": {"on_fail": ["denied"]},
            },
        ],
        "outputs": {
            "judgement.json": "judgement",
            "policy.json": "policy_result",
            "runbook_evidence.json": "runbook_evidence",
        },
    },
}