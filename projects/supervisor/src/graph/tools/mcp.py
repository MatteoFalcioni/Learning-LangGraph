# here we use the github mcp server
import os
from langchain_mcp_adapters.client import MultiServerMCPClient  

class GitHubMCPTools:
    def __init__(self):
        self.client = MultiServerMCPClient({
            "github": {
                "transport": "http",
                "url": "https://api.githubcopilot.com/mcp/x/notifications",  # https://github.com/github/github-mcp-server/blob/main/docs/remote-server.md
                "headers": {
                        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"
                    },
                
            }
        })
    
    async def get_tools(self):
        return await self.client.get_tools()


# use it as:
# github_mcp = GitHubMCPTools
# github_tools = await github_mcp.get_tools()