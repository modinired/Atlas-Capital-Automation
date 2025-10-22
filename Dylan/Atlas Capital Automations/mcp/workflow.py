"""
Workflow MCP
-----------

This module provides utilities to compile and execute task DAGs as
described by Card descriptors.  Tasks are executed sequentially in
the order they appear.  Each task defines a ``tool`` name,
positional and keyword arguments under ``args``, and an optional
``save_as`` key to persist the result in the execution context for
later steps.  Tasks may also specify a ``gate`` object controlling
flow based on policy enforcement results.

Supported tool prefixes correspond to the other MCP modules:

* ``knowledge.ground`` – calls :func:`mcp.knowledge.ground`.
* ``knowledge.writeback`` – calls :func:`mcp.knowledge.writeback`.
* ``triangulator.route`` – calls :func:`mcp.triangulator.route`.
* ``triangulator.adjudicate`` – calls :func:`mcp.triangulator.adjudicate`.
* ``triangulator.self_check`` – calls :func:`mcp.triangulator.self_check`.
    * ``policy.enforce`` – calls :func:`mcp.policy.enforce`.
    * ``policy.redact`` – calls :func:`mcp.policy.redact`.
    * ``codeexec.execute`` – calls :func:`mcp.codeexec.execute`.

New tool families can be integrated by extending the mapping in
``_TOOL_REGISTRY``.

Execution context is stored in a dictionary.  Variable references
inside ``args`` values are resolved via Python string formatting
with the context dictionary.  For example, if a task has

    args: { "query": "risk of ${vendor_id}", "space": "third_party" }

and the context contains ``vendor_id = "acme_corp"``, the
placeholder will be replaced with ``"risk of acme_corp"``.  Lists
and nested dictionaries are resolved recursively.

Tasks can define a ``gate`` key with a dictionary specifying
conditions to halt execution.  If the preceding tool returns a
dictionary containing ``status`` equal to ``"denied"`` (or any
status listed under ``gate['on_fail']``), the workflow will
terminate early and return the current context.  This is used by
Policy MCP to enforce PII redaction or other constraints.

Example Card execution::

    from mcp.cards import CARDS
    from mcp.workflow import run_card
    result = run_card(CARDS['QBR'], inputs={'accounts': ['ACME']})
    print(result['dossier'])

"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Callable, Dict, List, Optional

from . import knowledge, triangulator, policy, codeexec


# Map tool names to callables.  The values are functions that accept
# keyword arguments and return either a result or a coroutine.  If the
# function is asynchronous it will be awaited automatically.
_TOOL_REGISTRY: Dict[str, Callable[..., Any]] = {
    "knowledge.ground": knowledge.ground,
    "knowledge.writeback": knowledge.writeback,
    "triangulator.route": triangulator.route,
    "triangulator.adjudicate": triangulator.adjudicate,
    "triangulator.self_check": triangulator.self_check,
    "policy.enforce": policy.enforce,
    "policy.redact": policy.redact,
    # Code execution service.  Allows tasks to execute sandboxed code snippets.
    "codeexec.execute": None,  # placeholder; will be replaced after import
}

# Replace the placeholder entry with the actual function after import.  This
# indirection avoids circular import issues during module initialisation.
_TOOL_REGISTRY["codeexec.execute"] = codeexec.execute


def _deep_resolve(value: Any, context: Dict[str, Any]) -> Any:
    """Recursively resolve placeholders in the value using the context.

    Strings containing ``${var}`` will be replaced with the
    corresponding value from the context if present.  Dictionaries
    and lists are traversed recursively.  Scalar values are returned
    unchanged.

    Parameters
    ----------
    value : Any
        The value to resolve.
    context : dict
        Dictionary containing previously saved values.

    Returns
    -------
    Any
        The resolved value.
    """
    if isinstance(value, str):
        # If the entire string is a single variable reference, return the
        # referenced object directly without string conversion.
        full_var_match = re.fullmatch(r"\$\{([^}]+)\}", value)
        if full_var_match:
            key = full_var_match.group(1)
            return context.get(key, value)
        # Otherwise perform textual substitution.  Unmatched variables
        # remain unchanged.
        def replacer(match: re.Match) -> str:
            key = match.group(1)
            return str(context.get(key, match.group(0)))
        return re.sub(r"\$\{([^}]+)\}", replacer, value)
    elif isinstance(value, dict):
        return {k: _deep_resolve(v, context) for k, v in value.items()}
    elif isinstance(value, list):
        return [_deep_resolve(item, context) for item in value]
    else:
        return value


def _is_coroutine(func: Callable[..., Any]) -> bool:
    """Return True if calling ``func`` returns an awaitable."""
    return asyncio.iscoroutinefunction(func)


async def _call_tool(name: str, args: Dict[str, Any]) -> Any:
    """Invoke a tool by name with resolved arguments.

    The function looks up the tool in the registry and calls it.  If
    the tool is asynchronous, it is awaited.
    """
    if name not in _TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {name}")
    func = _TOOL_REGISTRY[name]
    result = func(**args)  # type: ignore[misc]
    if asyncio.iscoroutine(result):
        result = await result
    return result


async def run_workflow(tasks: List[Dict[str, Any]], inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a sequence of tasks defined in a Card descriptor.

    Parameters
    ----------
    tasks : list of dict
        Each task must include at least a ``tool`` key and may
        optionally include ``args``, ``save_as`` and ``gate`` keys.
    inputs : dict
        Dictionary of initial values injected into the execution
        context.  These values may be referenced in later task
        argument placeholders.

    Returns
    -------
    dict
        A context dictionary containing all saved values and the
        outputs of the tasks.  If execution was gated, the context
        reflects the state at termination.
    """
    context: Dict[str, Any] = {}
    context.update(inputs)
    for task in tasks:
        tool_name: str = task["tool"]
        args: Dict[str, Any] = task.get("args", {})
        # Resolve variables in args using the current context
        resolved_args = _deep_resolve(args, context)
        result = await _call_tool(tool_name, resolved_args)
        save_as: Optional[str] = task.get("save_as")
        if save_as:
            context[save_as] = result
        # Apply gate logic: if the task defines a gate and the result
        # contains a status listed under on_fail, stop execution.
        gate = task.get("gate")
        if gate and isinstance(result, dict):
            on_fail = gate.get("on_fail")
            if on_fail and result.get("status") in on_fail:
                context["halt_reason"] = f"Gate triggered on {tool_name}"
                break
    return context


async def run_card(card: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Execute an entire Card given its descriptor and input values.

    Cards are defined in the ``mcp.cards`` module.  The descriptor
    should contain a ``plan`` key with the list of tasks and an
    ``outputs`` key listing the names of context variables to include
    in the final dossier.  After running the workflow, this function
    assembles the final outputs and returns them along with the
    execution context.
    """
    tasks: List[Dict[str, Any]] = card.get("plan", [])
    context = await run_workflow(tasks, inputs)
    outputs_spec: Dict[str, str] = card.get("outputs", {})
    dossier: Dict[str, Any] = {}
    for name, ref in outputs_spec.items():
        # Allow dot notation for nested contexts, e.g. `${result.key}`
        value = context.get(ref)
        dossier[name] = value
    context["dossier"] = dossier
    return context