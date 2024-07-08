import asyncio
from typing import Tuple

from agnext.core import CancellationToken

from .base_agent import BaseAgent, UserContent


class UserProxy(BaseAgent):
    """An agent that allows the user to play the role of an agent in the conversation."""

    DEFAULT_DESCRIPTION = "A human user."

    def __init__(
        self,
        description: str = DEFAULT_DESCRIPTION,
    ) -> None:
        super().__init__(description)

    async def _generate_reply(self, cancellation_token: CancellationToken) -> Tuple[bool, UserContent]:
        """Respond to a reply request."""
        # Make an inference to the model.
        response = await self.ainput("User input ('exit' to quit): ")
        response = response.strip()
        return response == "exit", response

    async def ainput(self, prompt: str) -> str:
        return await asyncio.to_thread(input, f"{prompt} ")
