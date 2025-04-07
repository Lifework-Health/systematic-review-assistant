import asyncio
import contextvars
import threading
import typing as t

from pydantic import BaseModel, ConfigDict
from streamlit.runtime.scriptrunner_utils.script_run_context import (
    get_script_run_ctx,
)

from sr_assistant.app.config import get_settings

logger = get_settings().logger

app_context = contextvars.ContextVar("app_context")

class AppCtx(BaseModel):
    """Application context, synced with Streamlit.

    Also manages threading/asyncio tasks, etc., and provides context to LangChain
    runnables and LangGraph agents which may run in threads or asyncio tasks/coros.
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        from_attributes=True,
        )
    streamlit_script_run_ctx: t.ClassVar[ContextVar] = contextvars.ContextVar("streamlit_script_run_ctx")
    @computed_field
    def streamlit_ctx(self, t: threading.Thread | None, coro: t.Coroutine | None, task: asyncio.Task | None, tg: asyncio.TaskGroup | None, loop: asyncio.AbstractEventLoop) -> ContetxVar:
        ctx = get_script_run_ctx()
        logger.info(f"script_run_ctx: {ctx}")
        self.streamlit_script_run_ctx = ctx
        return ctx
