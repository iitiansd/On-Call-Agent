from enum import Enum, auto
from typing import Dict, List, Union, Callable
from pydantic import BaseModel, Field
from langchain.llms import OpenAI
from app.services.jiratool import JiraHandler
from app.services.observe_logs import ObserveLogsFetcher
from app.services.chat import ChatService
from app.schemas.chat import ChatRequest
from app.core.config import settings
import json


class Name(Enum):
    """Available tools for the incident management agent"""
    JIRA = auto()
    CHAT = auto() 
    OBSERVE = auto()
    NONE = auto()

    def __str__(self) -> str:
        return self.name.lower()

class Tool:
    """Tool wrapper for incident management functions"""
    def __init__(self, name: Name, func: Callable):
        self.name = name
        self.func = func
    
    def use(self, **kwargs) -> Union[str, Exception]:
        try:
            return self.func(**kwargs)
        except Exception as e:
            return str(e)

class IncidentAgent:
    """ReAct agent for incident management with OpenAI"""
    def __init__(self):
        self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.tools: Dict[Name, Tool] = {}
        self.messages = []
        self.current_iteration = 0
        self.max_iterations = 5
        
        # Initialize services
        self.jira_handler = JiraHandler()
        self.observe_logs = ObserveLogsFetcher()
        self.chat_service = ChatService()
        
        # Store context between tool calls
        self.context = {}
        
        # Register all tools
        self.register_tools()
        
    def register_tools(self):
        """Register all available tools"""
        self.register(Name.JIRA, self._handle_jira)
        self.register(Name.CHAT, self._handle_chat)
        self.register(Name.OBSERVE, self._handle_observe)
        
    def register(self, name: Name, func: Callable):
        """Register a single tool"""
        self.tools[name] = Tool(name, func)

    def _handle_jira(self, **kwargs) -> str:
        """
        Handle Jira ticket operations
        Expected kwargs: ticket_id
        """
        ticket_id = kwargs.get('ticket_id')
        if not ticket_id:
            return "Error: ticket_id is required"
            
        # Get ticket details including query_summary and observe_logs_url
        ticket_details = self.jira_handler.get_jira_details(ticket_id)
        
        # Store important information in context for other tools
        self.context.update({
            'query_summary': ticket_details.get('query_summary'),
            'observe_logs_url': ticket_details.get('observe_logs_url'),
            'summary': ticket_details.get('summary'),
        })
        
        # Search for similar issues using query_summary
        if ticket_details.get('query_summary'):
            similar_issues = self.jira_handler.search_issues_by_summary(ticket_details['query_summary'])
            ticket_details['similar_issues'] = similar_issues
            
        return json.dumps(ticket_details, indent=2)

    async def _handle_chat(self, **kwargs) -> str:
        """
        Handle chat service operations using query_summary
        Expected kwargs: organization_id, conversation_id
        Uses query_summary from context
        """
        query_summary = self.context.get('query_summary')
        if not query_summary:
            return "Error: No query_summary available. Run JIRA tool first."
            
        chat_request = ChatRequest(
            query=query_summary,
            organization_id=kwargs.get('organization_id', 'default'),
            conversation_id=kwargs.get('conversation_id', '1')
        )
        
        response = await self.chat_service.generate_response(chat_request)
        return json.dumps({
            'answer': response.answer,
            'relevant_docs': response.relevant_docs,
            'relevant_questions': response.relevant_questions
        }, indent=2)

    def _handle_observe(self, **kwargs) -> str:
        """
        Handle Observe logs operations
        Uses observe_logs_url from context
        """
        observe_logs_url = self.context.get('observe_logs_url')
        if not observe_logs_url:
            return "Error: No observe_logs_url available. Run JIRA tool first."
            
        logs = self.observe_logs.fetch_logs(observe_logs_url)
        return json.dumps(logs, indent=2)

    async def execute(self, ticket_id: str, organization_id: str = 'default', conversation_id: str = '1') -> str:
        """Main execution flow for incident analysis"""
        self.current_iteration = 0
        self.messages = []
        self.context = {
            'ticket_id': ticket_id,
            'organization_id': organization_id,
            'conversation_id': conversation_id
        }
        
        await self.think(self._format_prompt(f"Analyze Jira ticket: {ticket_id}"))
        return self.messages[-1]["content"] if self.messages else "Analysis failed"

    async def think(self, prompt: str) -> None:
        """Process current state and decide next action"""
        self.current_iteration += 1
        import pdb; pdb.set_trace()
        
        if self.current_iteration > self.max_iterations:
            self.trace("assistant", "Maximum iterations reached. Here's what I found so far...")
            return
            
        # response = self.llm.predict(prompt)
        response = self.llm.invoke(prompt)
        await self.decide(response)

    async def decide(self, response: str) -> None:
        """Parse response and execute next action"""
        try:
            import pdb; pdb.set_trace()
            parsed = json.loads(response)
            
            if "action" in parsed:
                action = parsed["action"]
                tool_name = Name[action["name"].upper()]
                
                if tool_name == Name.NONE:
                    self.trace("assistant", parsed.get("answer", "Analysis complete."))
                else:
                    self.trace("assistant", f"Using {tool_name} tool: {action.get('reason', '')}")
                    await self.act(tool_name)
                    
            elif "answer" in parsed:
                self.trace("assistant", parsed["answer"])
                
        except Exception as e:
            self.trace("assistant", f"Error processing response: {str(e)}")
            await self.think(self._format_prompt("Continue analysis"))

    async def act(self, tool_name: Name) -> None:
        """Execute selected tool with proper context"""
        tool = self.tools.get(tool_name)
        import pdb; pdb.set_trace()
        if tool:
            # Pass relevant context to each tool
            result = await tool.use(**self.context) if tool_name == Name.CHAT else tool.use(**self.context)
            self.trace("system", f"Result from {tool_name}: {result}")
            await self.think(self._format_prompt("Continue analysis"))
        else:
            self.trace("system", f"Tool {tool_name} not found")
            await self.think(self._format_prompt("Continue analysis"))

    def trace(self, role: str, content: str) -> None:
        """Record conversation history"""
        self.messages.append({"role": role, "content": content})

    def _format_prompt(self, query: str) -> str:
        """Format prompt for the LLM"""
        history = "\n".join([f"{m['role']}: {m['content']}" for m in self.messages])
        tools = ", ".join([str(tool.name) for tool in self.tools.values()])
        
        return f"""You are an incident management AI assistant. Analyze this situation:
    Query: {query}

    Current Context:
    - Ticket ID: {self.context.get('ticket_id')}
    - Query Summary: {self.context.get('query_summary', 'Not available yet')}
    - Observe Logs URL: {self.context.get('observe_logs_url', 'Not available yet')}

    Previous steps and observations:
    {history}

    Available tools: {tools}

   Instructions:
    1. Analyze the situation and previous observations.
    2. Choose the next action in this sequence:
    - Use JIRA tool first to get ticket details and similar issues.
    - After getting the response from JIRA Tool make call to CHAT tool to get relevant knowledge base information.
    - After you get a response from chat tool make call to OBSERVE tool to analyze logs if available.
    - Provide final analysis when enough information is gathered.

    Respond in JSON format:

    For using a tool:
    {{
        "thought": "Your reasoning for the next step",
        "action": {{
            "name": "Tool name (jira, chat, observe, or none)",
            "reason": "Why you chose this tool"
        }}
    }}

    For final answer:
    {{
        "thought": "Your analysis process",
        "answer": "Comprehensive analysis including:
                - Issue summary
                - Similar past incidents
                - Log analysis (if available)
                - Recommended solution
                - Prevention measures"
    }}

    Important:
    - Follow the tool sequence: JIRA -> CHAT -> OBSERVE.
    - Each tool needs specific data from previous tools.
    - Provide clear, actionable recommendations.
    - Always respond in valid JSON format.
    - If you are unsure, use the JIRA tool first to gather more information.
    """

async def run(ticket_id: str, organization_id: str = 'default', conversation_id: str = '1') -> str:
    """Initialize and run the incident management agent"""
    agent = IncidentAgent()
    return await agent.execute(ticket_id, organization_id, conversation_id)



import asyncio
from app.scripts.agent import run

async def main():
    ticket_id = "SLA-571468"
    organization_id = "default"
    conversation_id = "1"
    result = await run(ticket_id, organization_id, conversation_id)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())