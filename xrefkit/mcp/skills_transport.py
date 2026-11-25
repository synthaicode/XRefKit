"""Local SEP-2640 request binding for the MCP 1.28 / 2025-11-25 SDK.

The SDK's closed request union needs a session-local extension. Keep this
compatibility code separate from catalog logic; never patch SDK globals.
"""
from __future__ import annotations

from contextlib import AsyncExitStack
import logging
from typing import Any, Literal

import anyio
from mcp import types
from mcp.server.fastmcp import FastMCP
from mcp.server.lowlevel import Server
from mcp.server.session import ServerSession
from pydantic import StrictStr, field_validator

from .skills_extension import EXTENSION_ID, SkillsExtension

LOGGER = logging.getLogger(__name__)


class ListSkillsParams(types.RequestParams):
    cursor: StrictStr | None = None

    @field_validator("cursor", mode="before")
    @classmethod
    def cursor_must_be_a_string_when_present(cls, value: Any) -> Any:
        if value is None:
            raise ValueError("cursor must be a string when present")
        return value


class ListSkillsRequest(types.Request):
    method: Literal["skills/list"] = "skills/list"
    params: ListSkillsParams | None = None


class GetSkillParams(types.RequestParams):
    uri: StrictStr


class GetSkillRequest(types.Request):
    method: Literal["skills/get"] = "skills/get"
    params: GetSkillParams


class SkillsClientRequest(types.ClientRequest):
    # Retain the SDK wrapper identity used by Server._handle_message.
    root: types.ClientRequestType | ListSkillsRequest | GetSkillRequest


class SkillsServerSession(ServerSession):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._receive_request_type = SkillsClientRequest


class SkillsServer(Server):
    def get_capabilities(self, notification_options: Any, experimental_capabilities: Any) -> types.ServerCapabilities:
        capabilities = super().get_capabilities(notification_options, experimental_capabilities)
        capabilities.resources = capabilities.resources or types.ResourcesCapability()
        capabilities.extensions = {EXTENSION_ID: {}}
        return capabilities

    async def run(self, read_stream: Any, write_stream: Any, initialization_options: Any,
                  raise_exceptions: bool = False, stateless: bool = False) -> None:
        # Mirrors SDK 1.28 Server.run only to select our session parser. All
        # message handling, request context and protocol gates remain SDK-owned.
        async with AsyncExitStack() as stack:
            lifespan_context = await stack.enter_async_context(self.lifespan(self))
            session = await stack.enter_async_context(SkillsServerSession(
                read_stream, write_stream, initialization_options, stateless=stateless,
            ))
            task_support = self._experimental_handlers.task_support if self._experimental_handlers else None
            if task_support is not None:
                task_support.configure_session(session, stateless=stateless)
                await stack.enter_async_context(task_support.run())
            async with anyio.create_task_group() as group:
                try:
                    async for message in session.incoming_messages:
                        group.start_soon(self._handle_message, message, session, lifespan_context, raise_exceptions)
                finally:
                    group.cancel_scope.cancel()


class SkillsFastMCP(FastMCP):
    def _setup_handlers(self) -> None:
        original = self._mcp_server
        self._mcp_server = SkillsServer(
            original.name, version=original.version, instructions=original.instructions,
            website_url=original.website_url, icons=original.icons, lifespan=original.lifespan,
        )
        super()._setup_handlers()


def install_skills_handlers(app: SkillsFastMCP, extension: SkillsExtension) -> None:
    server = app._mcp_server
    previous_read = server.request_handlers[types.ReadResourceRequest]
    previous_list = server.request_handlers[types.ListResourcesRequest]

    async def result(operation: Any, *args: Any) -> types.ServerResult:
        try:
            payload = await anyio.to_thread.run_sync(operation, *args)
            return types.ServerResult(types.EmptyResult(**payload))
        except ValueError as exc:
            from mcp.shared.exceptions import McpError
            raise McpError(types.ErrorData(code=types.INVALID_PARAMS, message=str(exc))) from exc
        except Exception as exc:
            from mcp.shared.exceptions import McpError
            LOGGER.exception("Skills extension operation failed")
            raise McpError(types.ErrorData(code=types.INTERNAL_ERROR, message="Skills extension internal error")) from exc

    async def list_skills(request: ListSkillsRequest) -> types.ServerResult:
        return await result(extension.list_skills, request.params.cursor if request.params else None)

    async def get_skill(request: GetSkillRequest) -> types.ServerResult:
        return await result(extension.get_skill, request.params.uri)

    async def read_resource(request: types.ReadResourceRequest) -> types.ServerResult:
        uri = str(request.params.uri)
        if uri.startswith("skill:"):
            return await result(extension.read_resource, uri)
        return await previous_read(request)

    async def list_resources(request: types.ListResourcesRequest) -> types.ServerResult:
        previous = await previous_list(request)
        if request.params and request.params.cursor is not None:
            return previous
        additions = (await anyio.to_thread.run_sync(extension.list_resources))["resources"]
        previous.root.resources.extend(types.Resource(**item) for item in additions)
        return previous

    server.request_handlers[ListSkillsRequest] = list_skills
    server.request_handlers[GetSkillRequest] = get_skill
    server.request_handlers[types.ReadResourceRequest] = read_resource
    server.request_handlers[types.ListResourcesRequest] = list_resources
