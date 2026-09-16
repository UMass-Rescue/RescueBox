"""
Validation for CASE/UCO JSON-LD fragments built with ``case_uco.CASEGraph``.

Requires ``case-utils`` (``case_validate`` on PATH) for full SHACL checks — install with
``poetry install --with case-validation`` or ``pip install case-utils``.
"""

from __future__ import annotations

import json
from typing import Any

from case_uco import CASEGraph

from case_export.fragment import KB_PREFIX


def validate_fragment_jsonld(doc: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate ``doc`` using :meth:`CASEGraph.validate` (SHACL via ``case_validate``).

    Returns:
        ``(True, [message])`` on success or when validation is skipped (no ``case_validate``).
        ``(False, [error])`` when validation runs and fails.
    """
    try:
        g = CASEGraph(kb_prefix=KB_PREFIX)
        g.load(json.dumps(doc))
        out = g.validate()
        return True, [out.strip() if out else "CASE/UCO SHACL validation passed."]
    except RuntimeError as e:
        msg = str(e)
        if "case_validate not found" in msg or "case_validate" in msg.lower():
            return True, [
                "SHACL validation skipped: install case-utils "
                "(e.g. poetry install --with case-validation) so case_validate is on PATH."
            ]
        return False, [msg]
    except Exception as e:
        return False, [str(e)]
