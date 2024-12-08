import asyncio
import json
import logging
import warnings
from typing import Any, AsyncGenerator, Awaitable, Callable, Dict, List, Mapping, Sequence

from autogen_core import CancellationToken, FunctionCall
from autogen_core.components.models import (
    AssistantMessage,
    ChatCompletionClient,
    FunctionExecutionResult,
    FunctionExecutionResultMessage,
    LLMMessage,
    SystemMessage,
    UserMessage,
)
from autogen_core.components.models._types import CreateResult
from autogen_core.components.tools import FunctionTool, Tool
from typing_extensions import deprecated

from .. import EVENT_LOGGER_NAME
from ..base import Handoff as HandoffBase
from ..base import Response
from ..messages import (
    AgentMessage,
    ChatMessage,
    HandoffMessage,
    MultiModalMessage,
    TextMessage,
    ToolCallMessage,
    ToolCallResultMessage,
)
from ..state import AssistantAgentState
from ._base_chat_agent import BaseChatAgent

event_logger = logging.getLogger(EVENT_LOGGER_NAME)


@deprecated("Moved to autogen_agentchat.base.Handoff. Will remove in 0.4.0.", stacklevel=2)
class Handoff(HandoffBase):
    """[DEPRECATED] Handoff configuration. Moved to :class:`autogen_agentchat.base.Handoff`. Will remove in 0.4.0."""

    def model_post_init(self, __context: Any) -> None:
        warnings.warn(
            "Handoff was moved to autogen_agentchat.base.Handoff. Importing from this will be removed in 0.4.0.",
            DeprecationWarning,
            stacklevel=2,
        )


class AssistantAgent(BaseChatAgent):
    """An agent that provides assistance with tool use.

    ```{note}
    The assistant agent is not thread-safe or coroutine-safe.
    It should not be shared between multiple tasks or coroutines, and it should
    not call its methods concurrently.
    If multiple handoffs are detected, only the first handoff is executed.
    ```

    Args:
        name (str): The name of the agent.
        model_client (ChatCompletionClient): The model client to use for inference.
        tools (List[Tool | Callable[..., Any] | Callable[..., Awaitable[Any]]] | None, optional): The tools to register with the agent.
        handoffs (List[HandoffBase | str] | None, optional): The handoff configurations for the agent,
            allowing it to transfer to other agents by responding with a :class:`HandoffMessage`.
            The transfer is only executed when the team is in :class:`~autogen_agentchat.teams.Swarm`.
            If a handoff is a string, it should represent the target agent's name.
        description (str, optional): The description of the agent.
        system_message (str, optional): The system message for the model.
        max_tool_call_iterations (int, optional): The maximum number of attempts to run the model until the response is not a list of tool calls but a string.

    Raises:
        ValueError: If tool names are not unique.
        ValueError: If handoff names are not unique.
        ValueError: If handoff names are not unique from tool names.
        ValueError: If maximum number of tool iterations is less than 1.

    Examples:

        The following example demonstrates how to create an assistant agent with
        a model client and generate a response to a simple task.

        .. code-block:: python

            import asyncio
            from autogen_core import CancellationToken
            from autogen_ext.models import OpenAIChatCompletionClient
            from autogen_agentchat.agents import AssistantAgent
            from autogen_agentchat.messages import TextMessage


            async def main() -> None:
                model_client = OpenAIChatCompletionClient(
                    model="gpt-4o",
                    # api_key = "your_openai_api_key"
                )
                agent = AssistantAgent(name="assistant", model_client=model_client)

                response = await agent.on_messages(
                    [TextMessage(content="What is the capital of France?", source="user")], CancellationToken()
                )
                print(response)


            asyncio.run(main())


        The following example demonstrates how to create an assistant agent with
        a model client and a tool, generate a stream of messages for a task, and
        print the messages to the console.

        .. code-block:: python

            import asyncio
            from autogen_ext.models import OpenAIChatCompletionClient
            from autogen_agentchat.agents import AssistantAgent
            from autogen_agentchat.messages import TextMessage
            from autogen_agentchat.ui import Console
            from autogen_core import CancellationToken


            async def get_current_time() -> str:
                return "The current time is 12:00 PM."


            async def main() -> None:
                model_client = OpenAIChatCompletionClient(
                    model="gpt-4o",
                    # api_key = "your_openai_api_key"
                )
                agent = AssistantAgent(name="assistant", model_client=model_client, tools=[get_current_time])

                await Console(
                    agent.on_messages_stream(
                        [TextMessage(content="What is the current time?", source="user")], CancellationToken()
                    )
                )


            asyncio.run(main())


        The following example shows how to use `o1-mini` model with the assistant agent.

        .. code-block:: python

            import asyncio
            from autogen_core import CancellationToken
            from autogen_ext.models import OpenAIChatCompletionClient
            from autogen_agentchat.agents import AssistantAgent
            from autogen_agentchat.messages import TextMessage


            async def main() -> None:
                model_client = OpenAIChatCompletionClient(
                    model="o1-mini",
                    # api_key = "your_openai_api_key"
                )
                # The system message is not supported by the o1 series model.
                agent = AssistantAgent(name="assistant", model_client=model_client, system_message=None)

                response = await agent.on_messages(
                    [TextMessage(content="What is the capital of France?", source="user")], CancellationToken()
                )
                print(response)


            asyncio.run(main())

        .. note::

            The `o1-preview` and `o1-mini` models do not support system message and function calling.
            So the `system_message` should be set to `None` and the `tools` and `handoffs` should not be set.
            See `o1 beta limitations <https://platform.openai.com/docs/guides/reasoning#beta-limitations>`_ for more details.
    """

    def __init__(
        self,
        name: str,
        model_client: ChatCompletionClient,
        *,
        tools: List[Tool | Callable[..., Any] | Callable[..., Awaitable[Any]]] | None = None,
        handoffs: List[HandoffBase | str] | None = None,
        description: str = "An agent that provides assistance with ability to use tools.",
        system_message: str
        | None = "You are a helpful AI assistant. Solve tasks using your tools. Reply with TERMINATE when the task has been completed.",
        max_tool_call_iterations: int = 1,
    ):
        super().__init__(name=name, description=description)
        self._model_client = model_client
        if max_tool_call_iterations < 1:
            raise ValueError("The maximum number of tool iterations must be at least 1.")
        self._max_tool_call_iterations = max_tool_call_iterations
        if system_message is None:
            self._system_messages = []
        else:
            self._system_messages = [SystemMessage(content=system_message)]
        self._tools: List[Tool] = []
        if tools is not None:
            if model_client.capabilities["function_calling"] is False:
                raise ValueError("The model does not support function calling.")
            for tool in tools:
                if isinstance(tool, Tool):
                    self._tools.append(tool)
                elif callable(tool):
                    if hasattr(tool, "__doc__") and tool.__doc__ is not None:
                        description = tool.__doc__
                    else:
                        description = ""
                    self._tools.append(FunctionTool(tool, description=description))
                else:
                    raise ValueError(f"Unsupported tool type: {type(tool)}")
        # Check if tool names are unique.
        tool_names = [tool.name for tool in self._tools]
        if len(tool_names) != len(set(tool_names)):
            raise ValueError(f"Tool names must be unique: {tool_names}")
        # Handoff tools.
        self._handoff_tools: List[Tool] = []
        self._handoffs: Dict[str, HandoffBase] = {}
        if handoffs is not None:
            if model_client.capabilities["function_calling"] is False:
                raise ValueError("The model does not support function calling, which is needed for handoffs.")
            for handoff in handoffs:
                if isinstance(handoff, str):
                    handoff = HandoffBase(target=handoff)
                if isinstance(handoff, HandoffBase):
                    self._handoff_tools.append(handoff.handoff_tool)
                    self._handoffs[handoff.name] = handoff
                else:
                    raise ValueError(f"Unsupported handoff type: {type(handoff)}")
        # Check if handoff tool names are unique.
        handoff_tool_names = [tool.name for tool in self._handoff_tools]
        if len(handoff_tool_names) != len(set(handoff_tool_names)):
            raise ValueError(f"Handoff names must be unique: {handoff_tool_names}")
        # Check if handoff tool names not in tool names.
        if any(name in tool_names for name in handoff_tool_names):
            raise ValueError(
                f"Handoff names must be unique from tool names. Handoff names: {handoff_tool_names}; tool names: {tool_names}"
            )
        self._model_context: List[LLMMessage] = []
        self._is_running = False

    @property
    def produced_message_types(self) -> List[type[ChatMessage]]:
        """The types of messages that the assistant agent produces."""
        if self._handoffs:
            return [TextMessage, HandoffMessage]
        return [TextMessage]

    async def on_messages(self, messages: Sequence[ChatMessage], cancellation_token: CancellationToken) -> Response:
        async for message in self.on_messages_stream(messages, cancellation_token):
            if isinstance(message, Response):
                return message
        raise AssertionError("The stream should have returned the final result.")

    async def on_messages_stream(
        self, messages: Sequence[ChatMessage], cancellation_token: CancellationToken
    ) -> AsyncGenerator[AgentMessage | Response, None]:
        # Add messages to the model context.
        for msg in messages:
            if isinstance(msg, MultiModalMessage) and self._model_client.capabilities["vision"] is False:
                raise ValueError("The model does not support vision.")
            self._model_context.append(UserMessage(content=msg.content, source=msg.source))

        # Inner messages.
        inner_messages: List[AgentMessage] = []
        # Model response holder and tool call messages.
        result: CreateResult | None = None
        tool_call_msg: ToolCallMessage | None = None
        tool_call_result_msg: ToolCallResultMessage | None = None

        # call the model for _max_tool_call_iterations times or until the response is a string
        tool_call_iteration = 0
        while tool_call_iteration < self._max_tool_call_iterations:
            tool_call_iteration += 1
            # Generate an inference result based on the current model context.
            llm_messages = self._system_messages + self._model_context
            result = await self._model_client.create(
                llm_messages, tools=self._tools + self._handoff_tools, cancellation_token=cancellation_token
            )
            # Add the response to the model context.
            self._model_context.append(AssistantMessage(content=result.content, source=self.name))
            # check if the response is a list of tool calls and run the tool calls.
            if isinstance(result.content, str):
                break
            elif isinstance(result.content, list) and all(isinstance(item, FunctionCall) for item in result.content):
                tool_call_msg = ToolCallMessage(content=result.content, source=self.name, models_usage=result.usage)
                event_logger.debug(tool_call_msg)
                # Add the tool call message to the output.
                inner_messages.append(tool_call_msg)
                yield tool_call_msg

                # Execute the tool calls.
                results = await asyncio.gather(
                    *[self._execute_tool_call(call, cancellation_token) for call in result.content]
                )
                tool_call_result_msg = ToolCallResultMessage(content=results, source=self.name)
                event_logger.debug(tool_call_result_msg)
                self._model_context.append(FunctionExecutionResultMessage(content=results))
                inner_messages.append(tool_call_result_msg)
                yield tool_call_result_msg

                # Detect handoff requests.
                handoffs: List[HandoffBase] = []
                for call in result.content:
                    if call.name in self._handoffs:
                        handoffs.append(self._handoffs[call.name])
                if len(handoffs) > 0:
                    if len(handoffs) > 1:
                        # show warning if multiple handoffs detected
                        warnings.warn(
                            f"Multiple handoffs detected only the first is executed: {[handoff.name for handoff in handoffs]}",
                            stacklevel=2,
                        )
                    # Return the output messages to signal the handoff.
                    yield Response(
                        chat_message=HandoffMessage(
                            content=handoffs[0].message, target=handoffs[0].target, source=self.name
                        ),
                        inner_messages=inner_messages,
                    )
                    return

        assert result is not None
        # if last model response is a list of tool calls
        if isinstance(result.content, list) and all(isinstance(item, FunctionCall) for item in result.content):
            tool_call_summary = "Tool calls:"
            assert isinstance(tool_call_msg, ToolCallMessage)
            assert isinstance(tool_call_result_msg, ToolCallResultMessage)
            for i in range(len(tool_call_msg.content)):
                tool_call_summary += f"\n{tool_call_msg.content[i].name}({tool_call_msg.content[i].arguments}) = {tool_call_result_msg.content[i].content}"
            yield Response(
                chat_message=TextMessage(content=tool_call_summary, source=self.name, models_usage=result.usage),
                inner_messages=inner_messages,
            )
        # if last model response is a string
        else:
            assert isinstance(result.content, str)
            yield Response(
                chat_message=TextMessage(content=result.content, source=self.name, models_usage=result.usage),
                inner_messages=inner_messages,
            )

    async def _execute_tool_call(
        self, tool_call: FunctionCall, cancellation_token: CancellationToken
    ) -> FunctionExecutionResult:
        """Execute a tool call and return the result."""
        try:
            if not self._tools + self._handoff_tools:
                raise ValueError("No tools are available.")
            tool = next((t for t in self._tools + self._handoff_tools if t.name == tool_call.name), None)
            if tool is None:
                raise ValueError(f"The tool '{tool_call.name}' is not available.")
            arguments = json.loads(tool_call.arguments)
            result = await tool.run_json(arguments, cancellation_token)
            result_as_str = tool.return_value_as_string(result)
            return FunctionExecutionResult(content=result_as_str, call_id=tool_call.id)
        except Exception as e:
            return FunctionExecutionResult(content=f"Error: {e}", call_id=tool_call.id)

    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        """Reset the assistant agent to its initialization state."""
        self._model_context.clear()

    async def save_state(self) -> Mapping[str, Any]:
        """Save the current state of the assistant agent."""
        return AssistantAgentState(llm_messages=self._model_context.copy()).model_dump()

    async def load_state(self, state: Mapping[str, Any]) -> None:
        """Load the state of the assistant agent"""
        assistant_agent_state = AssistantAgentState.model_validate(state)
        self._model_context.clear()
        self._model_context.extend(assistant_agent_state.llm_messages)
