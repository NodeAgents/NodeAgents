#!/usr/bin/env python3 -m pytest

import unittest

import pytest
from conftest import MOCK_OPEN_AI_API_KEY

from autogen import GroupChat, GroupChatManager
from autogen.agentchat.contrib.llamaindex_conversable_agent import LLamaIndexConversableAgent
from autogen.agentchat.conversable_agent import ConversableAgent

try:
    from llama_index.core import Settings
    from llama_index.core.agent import ReActAgent
    from llama_index.core.agent.runner.base import AgentRunner
    from llama_index.core.chat_engine.types import AgentChatResponse
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.llms.openai import OpenAI
    from llama_index.tools.wikipedia import WikipediaToolSpec
except ImportError:
    skip = True
else:
    skip = False


@pytest.mark.skipif(skip, reason="dependency is not installed")
class TestLLamaIndexConversableAgent(unittest.TestCase):
    def setUp(self):
        llm = OpenAI(
            model="gpt-3.5-turbo-0125",
            temperature=0.0,
            api_key=MOCK_OPEN_AI_API_KEY,
        )

        embed_model = OpenAIEmbedding(
            model="text-embedding-ada-002",
            temperature=0.0,
            api_key=MOCK_OPEN_AI_API_KEY,
        )

        Settings.llm = llm
        Settings.embed_model = embed_model

        # create a react agent to use wikipedia tool
        wiki_spec = WikipediaToolSpec()
        # Get the search wikipedia tool
        wikipedia_tool = wiki_spec.to_tool_list()[1]

        location_specialist = ReActAgent.from_tools(tools=[wikipedia_tool], llm=llm, max_iterations=30, verbose=True)

        # create an autogen agent using the react agent
        trip_assistant = LLamaIndexConversableAgent(
            "trip_specialist",
            llama_index_agent=location_specialist,
            system_message="You help customers finding more about places they would like to visit. You can use external resources to provide more details as you engage with the customer.",
            description="This agents helps customers discover locations to visit, things to do, and other details about a location. It can use external resources to provide more details. This agent helps in finding attractions, history and all that there si to know about a place",
        )

        self.llamaidex_agent = trip_assistant

    def test_group_chat_with_lmm(self):
        """
        Tests the group chat functionality with two MultimodalConversable Agents.
        Verifies that the chat is correctly limited by the max_round parameter.
        Each agent is set to describe an image in a unique style, but the chat should not exceed the specified max_rounds.
        """

        llm_config = False
        max_round = 5

        user_proxy = ConversableAgent(
            "customer",
            description="This the customer trying to find information about Tokyo.",
            human_input_mode="ALWAYS",
        )

        group_chat = GroupChat(
            agents=[user_proxy, self.llamaidex_agent],
            messages=[],
            max_round=100,
            send_introductions=False,
        )

        group_chat_manager = GroupChatManager(
            groupchat=group_chat,
            llm_config=llm_config,
        )

        # Initiating the group chat and observing the number of rounds
        user_proxy.initiate_chat(
            group_chat_manager,
            message="What can i find in Tokyo related to Hayao Miyazaki and its moveis like Spirited Away?.",
        )

        # Assertions to check if the number of rounds does not exceed max_round
        assert all(
            len(arr) <= max_round for arr in self.llamaidex_agent._oai_messages.values()
        ), "Agent 1 exceeded max rounds"
        assert all(len(arr) <= max_round for arr in user_proxy._oai_messages.values()), "User proxy exceeded max rounds"
