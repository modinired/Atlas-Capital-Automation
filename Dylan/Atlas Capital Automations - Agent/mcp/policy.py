"""
Policy MCP
----------

This module implements a minimal Policy MCP responsible for enforcing
content policies and performing data redaction.  Policies can be
declared externally and referenced by ID; here we support a few
built‑in policies:

* ``"allow_all"`` – always permits the payload; returns ``status``
  ``"approved"``.
* ``"no_pii"`` – rejects payloads containing personally identifiable
  information (email addresses or social security numbers) unless
  redacted.  Returns ``status`` ``"denied"`` with details.

The primary functions are ``enforce`` and ``redact``.  Enforcement
returns a status and list of violations.  Redaction returns the
masked payload and a summary of replacements.  Both functions accept
arbitrary JSON‑serialisable objects (dicts, lists, strings).

This implementation uses regular expressions to detect PII.  In a
production system you would integrate with a dedicated DLP engine
such as Microsoft Presidio or a RuleSet from Open Policy Agent.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


# Regular expressions for simple PII detection.  These cover
# email addresses, US social security numbers, North American phone
# numbers and credit card numbers.  Additional patterns can be added
# as needed.
EMAIL_REGEX = re.compile(r"[\w.%-]+@[\w.-]+\.[A-Za-z]{2,}")
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
# Matches phone numbers in various North American formats such as
# 123-456-7890, (123) 456-7890, 123.456.7890, +1 123-456-7890.
PHONE_REGEX = re.compile(
    r"(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b"
)
# Matches potential credit card numbers: sequences of 13–19 digits separated
# by spaces or dashes.  A Luhn check is applied to confirm validity.
CREDIT_REGEX = re.compile(
    r"(?:\b(?:\d[ -]*?){13,19}\b)"
)


def _detect_pii(text: str) -> List[str]:
    """Find all PII substrings in the given text.

    Parameters
    ----------
    text : str
        Text to scan for PII patterns.

    Returns
    -------
    list of str
        All substrings that match PII patterns.
    """
    matches: List[str] = []
    matches.extend(EMAIL_REGEX.findall(text))
    matches.extend(SSN_REGEX.findall(text))
    matches.extend(PHONE_REGEX.findall(text))
    # Find candidate credit card numbers and validate with Luhn check
    for cand in CREDIT_REGEX.findall(text):
        # Remove spaces and dashes
        digits = re.sub(r"[ -]", "", cand)
        if 13 <= len(digits) <= 19 and _luhn_validate(digits):
            matches.append(cand)
    return matches


def _luhn_validate(number: str) -> bool:
    """Return True if the string of digits passes the Luhn check.

    Implements the Luhn algorithm to validate credit card numbers.

    Parameters
    ----------
    number : str
        String containing only digits.
    Returns
    -------
    bool
    """
    total = 0
    reverse_digits = list(map(int, reversed(number)))
    for idx, digit in enumerate(reverse_digits):
        if idx % 2 == 1:
            doubled = digit * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += digit
    return total % 10 == 0


def _mask_pii(text: str) -> Tuple[str, List[str]]:
    """Replace PII substrings in ``text`` with masked placeholders.

    Returns the masked text and a list of replaced substrings.
    """
    violations = _detect_pii(text)
    masked_text = text
    for item in violations:
        # Replace the PII with asterisks preserving length
        masked = "*" * len(item)
        masked_text = masked_text.replace(item, masked)
    return masked_text, violations


def redact(payload: Any, ruleset: str = "no_pii") -> Dict[str, Any]:
    """Redact sensitive fields in a payload according to a ruleset.

    The function recursively traverses dicts and lists.  Strings are
    scanned for PII patterns and masked.  Non‑string scalars are
    returned unchanged.

    Parameters
    ----------
    payload : Any
        Arbitrary JSON‑serialisable data.
    ruleset : str
        Identifier of the redaction ruleset.  Currently unused, but
        present to match the expected signature.  Future versions may
        support multiple rulesets.

    Returns
    -------
    dict
        Contains ``payload_redacted`` with the same structure as
        ``payload`` but with sensitive values masked, and
        ``mask_summary`` describing what was redacted.
    """
    if isinstance(payload, str):
        masked, violations = _mask_pii(payload)
        return {"payload_redacted": masked, "mask_summary": violations}
    elif isinstance(payload, dict):
        redacted_dict: Dict[str, Any] = {}
        summary: List[str] = []
        for k, v in payload.items():
            result = redact(v, ruleset)
            redacted_dict[k] = result["payload_redacted"]
            summary.extend(result["mask_summary"])
        return {"payload_redacted": redacted_dict, "mask_summary": summary}
    elif isinstance(payload, list):
        redacted_list: List[Any] = []
        summary: List[str] = []
        for item in payload:
            result = redact(item, ruleset)
            redacted_list.append(result["payload_redacted"])
            summary.extend(result["mask_summary"])
        return {"payload_redacted": redacted_list, "mask_summary": summary}
    else:
        return {"payload_redacted": payload, "mask_summary": []}


def enforce(payload: Any, policy_id: str = "no_pii") -> Dict[str, Any]:
    """Enforce a policy on the given payload.

    Parameters
    ----------
    payload : Any
        Data to check against the policy.  Can be a string, dict or list.
    policy_id : str
        Identifier of the policy to apply.  Supported policies are
        ``"allow_all"`` and ``"no_pii"``.

    Returns
    -------
    dict
        Contains ``status`` ("approved", "redacted" or "denied") and
        ``violations`` describing any issues found.  If redaction
        occurs, ``payload_redacted`` contains the masked payload.
    """
    if policy_id == "allow_all":
        return {"status": "approved", "violations": []}
    if policy_id == "no_pii":
        # Check for PII in the payload by serialising to a string
        # representation and scanning it.  For dicts and lists we use
        # repr(); this is a simple approach and should be replaced
        # with structured detection in production.
        serialized = repr(payload)
        violations = _detect_pii(serialized)
        if not violations:
            return {"status": "approved", "violations": []}
        # Perform redaction
        redacted = redact(payload, "no_pii")
        return {
            "status": "redacted",
            "violations": violations,
            "payload_redacted": redacted["payload_redacted"],
            "mask_summary": redacted["mask_summary"],
        }
    # Unknown policy
    return {"status": "unknown_policy", "violations": [f"Unsupported policy: {policy_id}"]}