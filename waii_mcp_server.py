import os
import json
import dotenv
from mcp.shared.exceptions import McpError
from mcp.server import FastMCP
from mcp.types import ErrorData, INVALID_PARAMS
from waii_sdk_py import WAII
from waii_sdk_py.chart import ChartType
from waii_sdk_py.chat import ChatRequest, ChatModule, ChatResponse

dotenv.load_dotenv(".env")
WAII_URL = os.getenv("WAII_URL")
DATABASE_KEY = os.getenv("DATABASE_KEY")
API_KEY = os.getenv("API_KEY")
MCP_PORT = os.getenv("MCP_PORT")

def apply_concierge_formatting(chat_response: ChatResponse):

    def concierge_widget(data: dict | list, data_type: str) -> str:
        serialized_data = json.dumps(
            dict(data_type=data_type, data=data),
            indent=2,
        )
        return f"\n%BEGIN_JSON%\n{serialized_data}\n%END_JSON%\n"

    try:
        references_section = ""
        if "<query>" in chat_response.response:
            references_section+=f"Generated query:\n```\n{chat_response.response_data.query.query}\n```\n"
        if "<data>" in chat_response.response:
            references_section += concierge_widget(chat_response.response_data.data.rows, data_type="table")
        if "<chart>" in chat_response.response:
            chart_spec = json.loads(chat_response.response_data.chart.chart_spec.chart)
            chart_spec["data"] = dict(values=chat_response.response_data.data.rows)
            references_section += concierge_widget(chart_spec, data_type="chart")
        return chat_response.response + "\n" + references_section
    except Exception as e:
        error_msg = f"Error processing chat response: {str(e)}"
        return f"Error processing response: {error_msg}"

class Chatbot:
    def __init__(self, url: str, api_key: str, database_key: str):
        try:
            print(f"Initializing WAII client with URL: {url}")
            # Initialize WAII client
            WAII.initialize(
                api_key=api_key,
                url=url,
            )
            print("Activating database connection...")
            WAII.database.activate_connection(database_key)
            print("Database connection activated successfully")
        except Exception as e:
            error_msg = f"Failed to initialize WAII client: {str(e)}"
            print(f"ERROR: {error_msg}")
            raise McpError(ErrorData(code=INVALID_PARAMS, message=error_msg))
        self.previous_chat_uuid = None
        self.enabled_chat_modules = [
            ChatModule.CONTEXT,
            ChatModule.TABLES,
            ChatModule.QUERY,
            ChatModule.DATA,
            ChatModule.CHART
        ]

    def ask_question(self, message: str) -> str:
        try:
            chat_response = WAII.chat.chat_message(ChatRequest(
                ask=message,
                parent_uuid=self.previous_chat_uuid,
                modules=self.enabled_chat_modules,
                chart_type=ChartType.VEGALITE,
            ))
            self.previous_chat_uuid = chat_response.chat_uuid
            response = apply_concierge_formatting(chat_response)
            return response
        except Exception as e:
            error_msg = f"Error asking question: {str(e)}"
            raise McpError(ErrorData(code=INVALID_PARAMS, message=error_msg))


def main():
    # Initialize FastMCP server
    mcp = FastMCP("waii", host='0.0.0.0', port=MCP_PORT)
    
    # Initialize chatbot
    chatbot = Chatbot(WAII_URL, API_KEY, DATABASE_KEY)

    @mcp.tool(
        name="movie_db_query_generator",
        description="Generate and run SQL queries and generate charts for the movies and tv database based on natural language questions. Includes information about genres, directors, actors, awards, keywords, finances, and more."
    )
    async def movie_db_query_generator(query: str) -> str:
        """Generate SQL queries for the movies and tv database based on natural language questions.

        Args:
            query: Natural language question about the movie and tv database (e.g. 'Show me all movies from 2023', 
                  'What are the top rated tv shows?', 'List movies directed by Christopher Nolan')
        """
        return chatbot.ask_question(query)

    # Start the server
    mcp.run(transport='streamable-http')

if __name__ == "__main__":
    main()
