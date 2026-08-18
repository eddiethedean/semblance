"""Named Foundry operations for CLI and compatibility lookup."""

from __future__ import annotations

from dataclasses import dataclass

from semblance_foundry.compatibility import operations_table


@dataclass(frozen=True)
class FoundryOperation:
    operation_id: str
    method: str
    path: str
    support_level: str


def registered_operations() -> list[FoundryOperation]:
    ops: list[FoundryOperation] = []
    for row in operations_table():
        ops.append(
            FoundryOperation(
                operation_id=str(row.get("operationId", "")),
                method=str(row.get("method", "")),
                path=str(row.get("path", "")),
                support_level=str(row.get("supportLevel", "")),
            )
        )
    return ops
