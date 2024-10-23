// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace AutoGen;

public class AssistantAgent : ConversableAgent
{
    public AssistantAgent(
            string name,
            string systemMessage = "You are a helpful AI assistant",
            ConversableAgentConfig? llmConfig = null,
            Func<IEnumerable<IMessage>, CancellationToken, Task<bool>>? isTermination = null,
            HumanInputMode humanInputMode = HumanInputMode.NEVER,
            IDictionary<string, Func<string, Task<string>>>? functionMap = null,
            string? defaultReply = null)
        : base(name: name,
         systemMessage: systemMessage,
         llmConfig: llmConfig,
         isTermination: isTermination,
         humanInputMode: humanInputMode,
         functionMap: functionMap,
         defaultReply: defaultReply)
    {
    }
}
