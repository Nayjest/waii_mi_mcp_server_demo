import asyncio
import os
import dotenv
import microcore as mc

dotenv.load_dotenv(".env")
MCP_URL = f"{os.getenv('MCP_HOST')}:{os.getenv('MCP_PORT')}/mcp"

print("Connecting to MCP server at:", mc.ui.cyan(MCP_URL))
mc.configure(
    MCP_SERVERS=[
        dict(name='waii', url=MCP_URL),
    ],
    EMBEDDING_DB_TYPE=""
)


async def main():
    try:
        mcp = await mc.mcp_server('waii').connect()
    except Exception as e:
        print(f"Error connecting to MCP server: {e}")
        return
    query = "Chart awards amount per year"
    response = await mcp.call('movie_db_query_generator', query=query, timeout=300)
    print('WAII:', response)
    await mcp.close()


asyncio.run(main())
