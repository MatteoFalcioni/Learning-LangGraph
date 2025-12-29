from typing import Annotated
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage, HumanMessage
from langgraph.types import Command

# helper function to create handoff tool
def create_handoff_tool(
    *, agent_name: str, description: str | None = None
):  #  * means: from here on, all arguments must be passed as keyword arguments
    name = f"transfer_to_{agent_name}"
    description = description or f"Ask {agent_name} for help."

    # the actual handoff tool
    @tool(name, description=description)
    def handoff_tool(
        task: Annotated[str, "The task that the subagent should perform"],
        runtime: ToolRuntime,
    ) -> Command:

        task_msg = HumanMessage(
            content=f"The agent supervisor advices you to perform the following task : \n{task}"
        )

        return Command(
            goto=agent_name,
            update={"messages": [task_msg]},
            graph=Command.PARENT,
        )

    return handoff_tool

handoff_to_gmail_agent = create_handoff_tool(agent_name="gmail_agent")
handoff_to_calendar_agent = create_handoff_tool(agent_name="calendar_agent")
handoff_to_github_agent = create_handoff_tool(agent_name="github_agent")
