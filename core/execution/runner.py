import time
import uuid
import logging
import httpx
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
from agents.shared.base import BaseAgent, AgentOutput
from core.storage.base import MetadataStore
from core.telemetry.tracing import get_tracer
from core.events.bus import event_bus
from core.execution.retry import RetryEngine

logger = logging.getLogger(__name__)
tracer = get_tracer(__name__)

class AgentRunner:
    def __init__(self, metadata_store: MetadataStore, retry_engine: Optional[RetryEngine] = None):
        self.metadata_store = metadata_store
        self.retry_engine = retry_engine or RetryEngine()

    async def run(self, agent: BaseAgent, input_data: Dict[str, Any], execution_id: Optional[str] = None) -> str:
        if not execution_id:
            execution_id = str(uuid.uuid4())
            # Save initial state if not already saved by caller (e.g. async route)
            await self.metadata_store.save_execution({
                "id": execution_id,
                "agent_name": agent.name,
                "status": "pending",
                "input_data": input_data,
                "start_time": datetime.utcnow()
            })

        await event_bus.emit("execution_started", {"execution_id": execution_id, "agent_name": agent.name})

        try:
            with tracer.start_as_current_span(f"agent_execution_{agent.name}") as span:
                span.set_attribute("execution_id", execution_id)

                await self.metadata_store.update_execution(execution_id, {"status": "running"})

                # Step 1: Validate
                validated_input = await self._run_step(execution_id, "validate", agent.validate, input_data)

                # Step 2: Retrieve Context
                context = await self._run_step(execution_id, "retrieve_context", agent.retrieve_context, validated_input)

                # Step 3: Plan
                plan = await self._run_step(execution_id, "plan", agent.plan, context)

                # Step 4: Execute
                raw_output = await self._run_step(execution_id, "execute", agent.execute, plan, execution_id)

                # Step 5: Validate Output
                agent_output = await self._run_step(execution_id, "validate_output", agent.validate_output, raw_output)

                # Step 6: Persist
                await self._run_step(execution_id, "persist", agent.persist, agent_output, execution_id)

                # Final update
                end_time = datetime.utcnow()
                execution_info = await self.metadata_store.get_execution(execution_id)
                start_time = execution_info["start_time"]

                # Handle start_time being string or datetime
                if isinstance(start_time, str):
                    try:
                        start_time = datetime.fromisoformat(start_time)
                    except:
                        start_time = datetime.utcnow()

                duration = (end_time - start_time).total_seconds()

                status = "succeeded" if agent_output.success else "failed"
                await self.metadata_store.update_execution(execution_id, {
                    "status": status,
                    "output_data": agent_output.data,
                    "error_message": agent_output.error,
                    "end_time": end_time,
                    "duration_seconds": duration
                })

                await event_bus.emit("execution_finished", {
                    "execution_id": execution_id,
                    "status": status,
                    "agent_name": agent.name
                })

                # Handle callback
                if execution_info.get("callback_url"):
                    await self._send_callback(execution_info["callback_url"], {
                        "execution_id": execution_id,
                        "agent_id": agent.name,
                        "status": status,
                        "result": agent_output.data,
                        "error": None
                    })

                return execution_id

        except Exception as e:
            logger.exception(f"Execution {execution_id} failed")
            await self.metadata_store.update_execution(execution_id, {
                "status": "failed",
                "error_message": str(e),
                "end_time": datetime.utcnow()
            })
            await event_bus.emit("execution_failed", {
                "execution_id": execution_id,
                "error": str(e),
                "agent_name": agent.name
            })

            # Handle callback for failure
            execution_info = await self.metadata_store.get_execution(execution_id)
            if execution_info and execution_info.get("callback_url"):
                 await self._send_callback(execution_info["callback_url"], {
                        "execution_id": execution_id,
                        "agent_id": agent.name,
                        "status": "failed",
                        "result": None,
                        "error": {
                            "code": "AGENT_EXECUTION_FAILED",
                            "message": str(e),
                            "details": {}
                        }
                    })

            return execution_id

    async def _send_callback(self, callback_url: str, payload: Dict[str, Any]):
        """Send execution result to callback URL with retries."""
        logger.info(f"Sending callback to {callback_url} for execution {payload['execution_id']}")

        async with httpx.AsyncClient() as client:
            for attempt in range(3):
                try:
                    response = await client.post(callback_url, json=payload, timeout=10.0)
                    response.raise_for_status()
                    logger.info(f"Callback delivered successfully to {callback_url}")
                    return
                except Exception as e:
                    logger.warning(f"Callback attempt {attempt + 1} failed for {callback_url}: {e}")
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)

            logger.error(f"Callback failed after 3 attempts for {callback_url}")

    async def _run_step(self, execution_id: str, step_name: str, func: Any, *args, **kwargs) -> Any:
        step_id = str(uuid.uuid4())
        start_time = datetime.utcnow()

        await self.metadata_store.add_step(execution_id, {
            "id": step_id,
            "step_name": step_name,
            "status": "running",
            "start_time": start_time,
            "input_params": {"args": [str(a) for a in args], "kwargs": {k: str(v) for k, v in kwargs.items()}}
        })

        try:
            with tracer.start_as_current_span(f"step_{step_name}") as span:
                # Use retry engine for steps
                result = await self.retry_engine.execute_with_retry(func, *args, **kwargs)

                await self.metadata_store.update_step(step_id, {
                    "status": "completed",
                    "output_data": {"result": str(result)},
                    "end_time": datetime.utcnow()
                })
                return result
        except Exception as e:
            await self.metadata_store.update_step(step_id, {
                "status": "failed",
                "output_data": {"error": str(e)},
                "end_time": datetime.utcnow()
            })
            raise
