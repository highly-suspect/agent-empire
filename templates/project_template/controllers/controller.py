class Controller:
    def __init__(self, agent, memory, tools, config):
        self.agent = agent
        self.memory = memory
        self.tools = tools
        self.config = config
    
    async def process_query(self, query, session_id=None):
        context = await self._load_context(session_id, query)
        plan = await self._decide_plan(query, context)
        tool_results = await self._execute_tools(plan)
        response = await self._think(query, context, tool_results)
        await self._remember(session_id, query, response)
        return response
    
    async def _load_context(self, session_id, query):
        return {}
    
    async def _decide_plan(self, query, context):
        return {"action": "direct_response", "tools": []}
    
    async def _execute_tools(self, plan):
        return {}
    
    async def _think(self, query, context, tool_results):
        return await self.agent.run(query)
    
    async def _remember(self, session_id, query, response):
        pass