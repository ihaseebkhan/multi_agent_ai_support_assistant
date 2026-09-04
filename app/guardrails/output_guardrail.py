from __future__ import annotations

from agents import Agent, GuardrailFunctionOutput, RunContextWrapper, Runner
from agents.decorators import output_guardrail

from app.models import MODEL_CHOICE, GuardrailDecision, SupportContext

guardrail_agent = Agent(
    name="GuardrailReview",
    model=MODEL_CHOICE,
    instructions=(
        "Review the support response. Block it only when it exposes sensitive "
        "customer data, makes unsupported claims, gives unsafe account-change "
        "instructions, or is inappropriate for customer support. "
        "Return blocked=true when the response must not be shown."
    ),
    output_type=GuardrailDecision,
)


@output_guardrail
async def support_output_guardrail(
    ctx: RunContextWrapper[SupportContext],
    agent: Agent,
    output: object,
) -> GuardrailFunctionOutput:
    result = await Runner.run(
        guardrail_agent,
        str(output),
        context=ctx.context,
    )

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.blocked,
    )