from __future__ import annotations

import asyncio
import uuid

from agents import OutputGuardrailTripwireTriggered

from app.evals.cases import EVAL_CASES, EvalCase
from app.main import handle_customer_request
from app.models import ToolExecutionError


class EvalResult:
    def __init__(self, case: EvalCase) -> None:
        self.case = case
        self.failures: list[str] = []
        self.crashed = False

    @property
    def passed(self) -> bool:
        return not self.failures and not self.crashed


async def run_case(case: EvalCase) -> EvalResult:
    result = EvalResult(case)
    conversation_id = f"eval-{uuid.uuid4()}"

    try:
        outcome = await handle_customer_request(
            message=case.input,
            conversation_id=conversation_id,
            customer_id=case.customer_id,
        )
    except OutputGuardrailTripwireTriggered:
        if not case.expect_guardrail_block:
            result.failures.append("guardrail blocked an unexpected response")
        return result
    except ToolExecutionError:
        if not case.expect_tool_error:
            result.failures.append("unexpected ToolExecutionError")
        return result
    except Exception as exc:  # noqa: BLE001 - eval must capture any crash, not just known ones
        result.crashed = True
        result.failures.append(f"unhandled exception: {exc!r}")
        return result

    if case.expect_guardrail_block:
        result.failures.append("expected guardrail to block, but got a normal response")
    if case.expect_tool_error:
        result.failures.append("expected a tool error, but got a normal response")

    if case.expected_intent is not None and outcome.intent != case.expected_intent:
        result.failures.append(
            f"intent mismatch: expected {case.expected_intent!r}, got {outcome.intent!r}"
        )

    if case.expected_agent is not None and outcome.selected_agent != case.expected_agent:
        result.failures.append(
            f"agent mismatch: expected {case.expected_agent!r}, got {outcome.selected_agent!r}"
        )

    for tool_name in case.expected_tools:
        if tool_name not in outcome.tools_used:
            result.failures.append(f"expected tool {tool_name!r} not in tools_used {outcome.tools_used}")

    answer_lower = outcome.answer.lower()
    for term in case.must_include_terms:
        if term.lower() not in answer_lower:
            result.failures.append(f"missing required term: {term!r}")

    for term in case.must_not_include_terms:
        if term.lower() in answer_lower:
            result.failures.append(f"forbidden term present: {term!r}")

    return result


async def main() -> None:
    results = [await run_case(case) for case in EVAL_CASES]

    print(f"{'CASE':40} {'STATUS':6} SAFETY_BEHAVIOR")
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{result.case.id:40} {status:6} {result.case.safety_behavior}")
        for failure in result.failures:
            print(f"    - {failure}")

    passed = sum(1 for r in results if r.passed)
    print(f"\n{passed}/{len(results)} eval cases passed")


if __name__ == "__main__":
    asyncio.run(main())