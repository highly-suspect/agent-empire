from pydantic_ai import Agent
from dotenv import load_dotenv

class BaseAgent:
    def __init__(self, name, system_prompt, config=None):
        load_dotenv()
        self.name = name
        self.config = config or {}
        model = self.config.get('model', 'openai:gpt-4o-mini')
        temperature = self.config.get('temperature', 0.2)
        
        self.agent = Agent(
            model,
            system_prompt=system_prompt,
            model_settings={'temperature': temperature}
        )
    
    async def run(self, query):
        result = await self.agent.run(query)
        return result.data