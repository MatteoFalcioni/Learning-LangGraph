from langchain.agents import AgentState

class SupervisorState(AgentState):
    file_system: dict[str, str]