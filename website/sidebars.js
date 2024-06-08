/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */

module.exports = {
  docsSidebar: [
    "Getting-Started",
    {
      type: "category",
      label: "Installation",
      collapsed: true,
      items: ["installation/Docker", "installation/Optional-Dependencies"],
      link: {
        type: "doc",
        id: "installation/Installation",
      },
    },
    {
      type: "category",
      label: "Tutorial",
      collapsed: false,
      link: {
        type: "generated-index",
        title: "Tutorial",
        description: "Tutorial on the basic concepts of AutoGen",
        slug: "tutorial",
      },
      items: [
        {
          type: "doc",
          id: "tutorial/introduction",
          label: "Introduction",
        },
        {
          type: "doc",
          id: "tutorial/chat-termination",
          label: "Chat Termination",
        },
        {
          type: "doc",
          id: "tutorial/human-in-the-loop",
          label: "Human in the Loop",
        },
        {
          type: "doc",
          id: "tutorial/code-executors",
          label: "Code Executors",
        },
        {
          type: "doc",
          id: "tutorial/tool-use",
          label: "Tool Use",
        },
        {
          type: "doc",
          id: "tutorial/conversation-patterns",
          label: "Conversation Patterns",
        },
        {
          type: "doc",
          id: "tutorial/what-next",
          label: "What Next?",
        },
      ],
    },
    { "Use Cases": [{ type: "autogenerated", dirName: "Use-Cases" }] },
    {
      type: "category",
      label: "User Guide",
      collapsed: false,
      link: {
        type: "generated-index",
        title: "User Guide",
        slug: "topics",
      },
      items: [{ type: "autogenerated", dirName: "topics" }],
    },
    {
      type: "link",
      label: "API Reference",
      href: "/docs/reference/agentchat/conversable_agent",
    },
    {
      type: "doc",
      label: "FAQs",
      id: "FAQ",
    },

    {
      type: "category",
      label: "AutoGen Studio",
      collapsed: true,
      items: ["autogen-studio/usage", "autogen-studio/faqs"],
      link: {
        type: "doc",
        id: "autogen-studio/getting-started",
      },
    },
    {
      type: "category",
      label: "Ecosystem",
      link: {
        type: "generated-index",
        title: "Ecosystem",
        description: "Learn about the ecosystem of AutoGen",
        slug: "ecosystem",
      },
      items: [{ type: "autogenerated", dirName: "ecosystem" }],
    },
    {
      type: "category",
      label: "Contributor Guide",
      collapsed: true,
      items: [{ type: "autogenerated", dirName: "contributor-guide" }],
      link: {
        type: "generated-index",
        title: "Contributor Guide",
        description: "Learn how to contribute to AutoGen",
        slug: "contributor-guide",
      },
    },
    "Research",
    "Migration-Guide",
  ],
  // pydoc-markdown auto-generated markdowns from docstrings
  referenceSideBar: [require("./docs/reference/sidebar.json")],
  notebooksSidebar: [
    {
      type: "category",
      label: "Notebooks",
      items: [
        {
          type: "autogenerated",
          dirName: "notebooks",
        },
      ],
      link: {
        type: "doc",
        id: "notebooks",
      },
    },
  ],
};
