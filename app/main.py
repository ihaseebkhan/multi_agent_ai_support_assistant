from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agents import OutputGuardrailTripwireTriggered, Runner

from app.agents.hooks import SupportRunHooks
from app.agents.triage_agent import triage_agent
from app.models import FinalAnswer, SupportContext, ToolExecutionError

app = FastAPI()


class AgentRequest(BaseModel):
    customer_id: int
    conversation_id: str
    message: str


class AgentResponse(BaseModel):
    conversation_id: str
    intent: str
    selected_agent: str
    answer: str
    confidence: float
    tools_used: list[str]
    citations: list[str]
    next_action: str
    guardrail_result: dict


async def handle_customer_request(
    message: str,
    conversation_id: str,
    customer_id: int,
) -> FinalAnswer:
    context = SupportContext(
        customer_id=customer_id,
        conversation_id=conversation_id,
    )

    result = await Runner.run(
        triage_agent,
        message,
        context=context,
        hooks=SupportRunHooks(),
    )

    return FinalAnswer(
        answer=str(result.final_output),
        selected_agent=result.last_agent.name,
        tools_used=context.used_tools,
        citations=context.citations,
        intent=context.intent,
        confidence=context.confidence,
    )


@app.post("/agent/respond", response_model=AgentResponse)
async def agent_respond(req: AgentRequest) -> AgentResponse:
    try:
        result = await handle_customer_request(
            message=req.message,
            conversation_id=req.conversation_id,
            customer_id=req.customer_id,
        )
    except OutputGuardrailTripwireTriggered:
        return AgentResponse(
            conversation_id=req.conversation_id,
            intent="guardrail_review",
            selected_agent="GuardrailReview",
            answer=(
                "I'm sorry, but I wasn't able to complete your request at this time."
                "Please try again or contact support for further assistance."
            ),
            confidence=1.0,
            tools_used=[],
            citations=[],
            next_action="response_withheld",
            guardrail_result={
                "passed": False,
                "flags": ["output_guardrail_triggered"],
            },
        )
    except ToolExecutionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return AgentResponse(
        conversation_id=req.conversation_id,
        intent=result.intent,
        selected_agent=result.selected_agent,
        answer=result.answer,
        confidence=result.confidence,
        tools_used=result.tools_used,
        citations=result.citations,
        next_action="response_sent",
        guardrail_result={"passed": True, "flags": []},
    )