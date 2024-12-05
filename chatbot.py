from typing import Any, Dict
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import os
import json
import asyncio
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIAgentManager:
    def __init__(self, openai_api_key: str, model: str = "gpt-3.5-turbo"):
        self.openai_api_key = openai_api_key
        self.model = model
        self.tools = None
        self.llm = None
        self.agent = None
        self.agent_executor = None
    
    def load_apis(self):
        with open('db.json', 'r') as f:
            self.apis = json.load(f)['apis']

    def evaluate_response(self, query: str, response: Dict[str, Any]) -> float:
        """Evaluate API response relevance"""
        evaluation_prompt = f"""
        Given the query: {query}
        And the API response: {response}
        Rate the relevance from 0 to 1.
        Return only the number.
        """
        try:
            score = float(self.llm.predict(evaluation_prompt))
            return min(max(score, 0), 1)  # Ensure between 0 and 1
        except:
            return 0

    def check_stored_responses(self, query: str) -> Dict[str, Any]:
        try:
            best_response = None
            best_score = 0
            
            for filename in os.listdir('responses'):
                with open(os.path.join('responses', filename), 'r') as f:
                    stored_response = json.load(f)
                    score = self.evaluate_response(query, stored_response)
                    if score > best_score:
                        best_score = score
                        best_response = stored_response
            
            return best_response if best_score > 0.7 else None
        except Exception as e:
            logger.error(f"Error checking stored responses: {e}")
            return None

    def create_tool_for_api(self, stored_response: Dict[str, Any]) -> Tool:
        return Tool(
            name=f"api_{stored_response['api_name']}",
            func=lambda x: stored_response,
            description=f"Use this tool for queries about {stored_response['api_name']}"
        )

    async def initialize(self):
        try:
            self.llm = ChatOpenAI(
                temperature=0,
                model=self.model,
                api_key=self.openai_api_key
            )
            
            def dummy_tool(x):
                return "This is a dummy tool response"

            if self.tools is None or len(self.tools) == 0:
                self.tools = [Tool(
                        name="dummy_tool",
                        func=dummy_tool,
                        description="A dummy tool for initialization"
                    )]
            else:
                # Check if tool with same name already exists
                existing_tool_names = [tool.name for tool in self.tools]
                if "dummy_tool" not in existing_tool_names:
                    self.tools.append(
                        Tool(
                            name="dummy_tool",
                            func=dummy_tool,
                            description="A dummy tool for initialization"
                        )
                    )

            prompt = PromptTemplate.from_template(
                """You are a helpful assistant that answers questions about users and continents.
                Use the available tools to find information.
                You have access to the following tools: {tools}

                The available tools are: {tool_names}

                To use a tool, you MUST use the following format:
                Thought: I need to use X tool because...
                Action: the_tool_name
                Action Input: the input to the tool
                Observation: the result of the action

                When you have a final response:
                Thought: I have all the information I need...
                Final Answer: your response

                Current conversation:
                {chat_history}
                Human: {input}
                Assistant: Let me help you with that.
                {agent_scratchpad}"""
            )

            self.agent = create_react_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )

            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=True,
                max_iterations=3,
                handle_parsing_errors=True
            )

        except Exception as e:
            logger.error(f"Error in initialization: {e}")
            raise

    async def update_tools(self, new_tool: Tool):
        try:
            if self.tools is None:
                self.tools = []
            self.tools.append(new_tool)
            
            await self.initialize()
        except Exception as e:
            logger.error(f"Error updating tools: {e}")
            raise

class Chatbot:
    def __init__(self, openai_api_key: str):
        self.agent_manager = APIAgentManager(openai_api_key)
        self.initialized = False

    async def ensure_initialized(self):
        if not self.initialized:
            await self.agent_manager.initialize()
            self.initialized = True

    async def process_query(self, query: str) -> str:
        try:
            await self.ensure_initialized()
            
            stored_response = self.agent_manager.check_stored_responses(query)
            if stored_response:
                tool = self.agent_manager.create_tool_for_api(stored_response)
                await self.agent_manager.update_tools(tool)
                
                chat_history = []
                response = await self.agent_manager.agent_executor.ainvoke({
                    "input": query,
                    "chat_history": chat_history
                })
                
                return response["output"] if "output" in response else str(response)
            
            return "No suitable response found in stored responses."
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"An error occurred: {str(e)}"

async def async_main():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    logger.debug(f"Looking for .env file at: {env_path}")
    
    if os.path.exists(env_path):
        logger.debug(".env file found")
        load_dotenv(env_path)
    else:
        logger.warning(".env file not found!")
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        return

    chatbot = Chatbot(openai_api_key)
    print("Chatbot initialized. Type 'quit' to exit.")
    
    try:
        while True:
            query = input("You: ").strip()
            if query.lower() in ['quit', 'exit', 'bye']:
                break
                
            response = await chatbot.process_query(query)
            print(f"Bot: {response}")
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"\nError: {e}")

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()