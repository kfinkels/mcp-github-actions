"""Main entry point for the MCP GitHub Actions server."""

import asyncio
import logging
import sys
from .server import GitHubActionsServer

def main():
    """Main entry point for the CLI."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def run_server():
        """Run the MCP server."""
        server = GitHubActionsServer()
        await server.run()
    
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 