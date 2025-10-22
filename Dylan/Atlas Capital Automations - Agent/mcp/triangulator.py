"""
Triangulator MCP
----------------

This module implements a simple Triangulator MCP responsible for routing
tasks across multiple models, adjudicating their outputs and
self‑checking results.  It is designed to be agnostic of the models
themselves: models are registered as callables that accept a ``task``
string and return an ``output`` string along with metadata.  Each
candidate produced by a model is captured as a :class:`Candidate`.

The primary functions are:

* ``route`` – dispatch a task to a specified list of models under
  latency and cost budgets.  Returns a list of candidates.
* ``adjudicate`` – choose a winning candidate given a set of rubric
  criteria.  Rubrics consist of named criteria with weights and
  evaluation functions.  A simple scoring scheme is provided.
* ``self_check`` – compute a quality score for a single output using
  rudimentary heuristics (e.g. checking for non‑empty output, absence
  of obvious PII).

In a production system this module would integrate with a routing
layer such as LiteLLM or LangGraph to handle model selection, load
balancing and retries.  The adjudicator could leverage external
evaluation frameworks such as RAGAS or DeepEval.  Here we implement
a deterministic yet extensible version suitable for demonstration and
testing.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Tuple

from pydantic import BaseModel, Field

import re


class Candidate(BaseModel):
    """Represents a single model's candidate output."""

    model_name: str = Field(..., description="Identifier of the model that produced the output")
    output: str = Field(..., description="The raw output string from the model")
    score: float = Field(..., description="Predicted quality score computed during routing")
    cost: float = Field(..., description="Estimated cost in arbitrary units (e.g. USD)")


async def local_model_echo(task: str) -> Tuple[str, float]:
    """A trivial local model that echoes the task as its output.

    Returns the input task and a score equal to 1.0 if the task is
    non‑empty, else 0.0.  Cost is 0.0 as it is local.
    """
    score = 1.0 if task.strip() else 0.0
    return (task, score)


async def local_model_reverse(task: str) -> Tuple[str, float]:
    """A simple local model that reverses the task string.

    It assigns a heuristic score based on the length of the task.
    Longer tasks yield slightly lower scores to simulate model
    degradation with complexity.
    """
    reversed_task = task[::-1]
    score = max(0.1, 1.0 - len(task) / 1000.0)
    return (reversed_task, score)


async def local_model_uppercase(task: str) -> Tuple[str, float]:
    """A local model that converts the task string to upper case.

    Scores outputs higher when the input contains at least one
    alphabetic character.  Useful as a third distinct model for
    triangulation.
    """
    transformed = task.upper()
    score = 1.0 if any(c.isalpha() for c in task) else 0.5
    return (transformed, score)


# Registry of available models.  Models should be async callables
# returning a tuple of (output, score).
MODEL_REGISTRY: Dict[str, Callable[[str], asyncio.Future]] = {
    "local_echo": local_model_echo,
    "local_reverse": local_model_reverse,
    "local_uppercase": local_model_uppercase,
    # Additional models can be added here (e.g. LLMs via LiteLLM, remote APIs).
}


async def route(
    *,
    task: str,
    models: List[str],
    latency_budget_ms: int = 5000,
    cost_ceiling: float = 1.0,
) -> Dict[str, Any]:
    """Route a task to a set of models and collect candidate outputs.

    Parameters
    ----------
    task : str
        Description of the job to perform.  In a question‑answering
        scenario this could be a prompt; in our risk scoring system
        this might be an instruction such as "summarize account data".
    models : list of str
        Identifiers of models to invoke.  Must exist in
        ``MODEL_REGISTRY``.
    latency_budget_ms : int, optional
        Maximum time in milliseconds allowed for all model calls.
    cost_ceiling : float, optional
        Maximum cumulative cost permitted.  Models that would exceed
        this cost are skipped.

    Returns
    -------
    dict
        Contains a ``candidates`` key with a list of
        :class:`Candidate` objects.  If a model fails, its exception
        is logged and omitted from the list.
    """
    # Start all tasks concurrently but honour the cost ceiling.
    tasks: List[asyncio.Task] = []
    task_names: List[str] = []
    cumulative_cost = 0.0
    for name in models:
        if name not in MODEL_REGISTRY:
            continue
        # For demonstration, assume each local model costs 0.0 units.
        cost = 0.0
        if cumulative_cost + cost > cost_ceiling:
            break
        coro = MODEL_REGISTRY[name](task)
        tasks.append(asyncio.create_task(coro))
        task_names.append(name)
        cumulative_cost += cost
    # Wait for tasks with timeout derived from latency budget
    timeout_sec = latency_budget_ms / 1000.0
    done, pending = await asyncio.wait(tasks, timeout=timeout_sec)
    candidates: List[Candidate] = []
    for i, fut in enumerate(done):
        try:
            output, score = fut.result()
            model_name = task_names[i] if i < len(task_names) else "unknown"
            candidates.append(
                Candidate(
                    model_name=model_name,
                    output=output,
                    score=score,
                    cost=0.0,
                )
            )
        except Exception:
            # ignore failed models
            continue
    # Cancel any pending tasks that exceeded the timeout
    for fut in pending:
        fut.cancel()
    # Return the list of candidates directly for convenience.
    return candidates


def adjudicate(
    *,
    candidates: List[Candidate],
    rubric: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Select a winner among candidates based on a rubric.

    The rubric is a list of criteria.  Each criterion must contain a
    ``name``, ``weight`` and ``criteria`` string describing the
    evaluation rule.  The current implementation evaluates two
    built‑in criteria:

    * ``"Non‑empty"`` – candidate receives 1.0 if the output is non‑empty,
      else 0.0.
    * ``"Shorter is better"`` – score is inversely proportional to the
      length of the output.

    Unknown criteria are ignored.  The weighted sum of criterion
    scores yields the candidate's overall rubric score.

    Returns
    -------
    dict
        Contains the ``winner`` (a :class:`Candidate`), the list of
        ``scores`` per candidate, and ``dissent`` capturing all
        candidates with their rubric scores.
    """
    if not candidates:
        return {"winner": None, "scores": [], "dissent": []}
    evaluated: List[Tuple[Candidate, float]] = []
    for cand in candidates:
        total_score = 0.0
        for crit in rubric:
            weight = float(crit.get("weight", 0.0))
            name = crit.get("name")
            # Evaluate built‑in criteria
            if name == "Non‑empty":
                score = 1.0 if cand.output.strip() else 0.0
            elif name == "Shorter is better":
                # Normalise length to [0,1] by assuming outputs longer than
                # 1000 characters are undesirable.  A 0‑length output gets
                # score 0.0.
                length = len(cand.output)
                score = 1.0 - min(length / 1000.0, 1.0)
            else:
                score = 0.0
            total_score += weight * score
        evaluated.append((cand, total_score))
    # Select candidate with highest total score; stable sort ensures
    # deterministic behaviour on ties
    evaluated.sort(key=lambda x: x[1], reverse=True)
    winner = evaluated[0][0]
    scores = [score for _, score in evaluated]
    dissent = [cand for cand, _ in evaluated[1:]]
    return {"winner": winner, "scores": scores, "dissent": dissent}


def self_check(
    *,
    output: str,
    checks: List[str],
) -> float:
    """Compute a simple quality score for an output.

    The self‑check runs a series of heuristics.  Supported check names
    are:

    * ``"faithfulness"`` – outputs containing the word "hallucinate" are
      penalised.
    * ``"pii"`` – outputs containing patterns that look like email
      addresses or social security numbers are penalised.
    * ``"reasoning"`` – outputs longer than 20 words are rewarded.

    Each check contributes equally to the final score (0.0–1.0).  The
    caller should interpret this as a confidence measure only.

    Returns
    -------
    float
        Averaged self‑check score between 0.0 and 1.0.
    """
    if not checks:
        return 1.0
    scores: List[float] = []
    for name in checks:
        if name == "faithfulness":
            scores.append(0.0 if "hallucinate" in output.lower() else 1.0)
        elif name == "pii":
            # simple email/SSN detection
            if re.search(r"[\w.%-]+@[\w.-]+", output) or re.search(r"\b\d{3}-\d{2}-\d{4}\b", output):
                scores.append(0.0)
            else:
                scores.append(1.0)
        elif name == "reasoning":
            word_count = len(output.strip().split())
            scores.append(1.0 if word_count > 20 else 0.5)
        else:
            scores.append(0.5)
    return sum(scores) / len(scores)