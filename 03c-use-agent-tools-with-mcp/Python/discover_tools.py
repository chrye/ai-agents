import os
from dotenv import load_dotenv

# Add references
from azure.identity import DefaultAzureCredential, AzureCliCredential, ChainedTokenCredential, InteractiveBrowserCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import McpTool, ToolSet, ListSortOrder, ToolApproval


# Load environment variables from .env file
load_dotenv()
project_endpoint = os.getenv("PROJECT_ENDPOINT_PERSONAL")
model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME")
funcapp_key = os.getenv("FUNCAPP_KEY")

# Validate required environment variables
if not project_endpoint:
    raise ValueError("PROJECT_ENDPOINT_PERSONAL not found in environment variables")
if not model_deployment:
    raise ValueError("MODEL_DEPLOYMENT_NAME not found in environment variables")
if not funcapp_key:
    raise ValueError("FUNCAPP_KEY not found in environment variables")

print(f"Using project endpoint: {project_endpoint}")
print(f"Using model deployment: {model_deployment}")
print(f"Function app key loaded: {'Yes' if funcapp_key else 'No'}")

# Connect to the agents client
try:
    # Use interactive browser authentication with the correct tenant
    credential = InteractiveBrowserCredential(
        tenant_id="7dbe1b65-a49a-420f-9c91-6bb67eeaa0d7"
    )
    
    agents_client = AgentsClient(
         endpoint=project_endpoint,
         credential=credential
    )
    print("Successfully created agents client with InteractiveBrowserCredential")
except Exception as auth_error:
    print(f"Authentication error: {auth_error}")
    print("Make sure you're logged into Azure CLI with 'az login' and have access to the AI Foundry project")
    exit(1)

# MCP server configuration
mcp_server_base_url = "https://mcp-client-management-func.azurewebsites.net/runtime/webhooks/mcp/sse"
mcp_server_url = f"{mcp_server_base_url}?code={funcapp_key}"
mcp_server_label = "mcp_clients_remote"  # Changed to use underscores instead of hyphens


# Initialize agent MCP tool
print(f"Setting up MCP tool for server: {mcp_server_label}")
print(f"MCP server URL: {mcp_server_url}")

mcp_tool = McpTool(
     server_label=mcp_server_label,
     server_url=mcp_server_url,
)
    
# Set approval mode to never require approval
mcp_tool.set_approval_mode("never")
    
toolset = ToolSet()
toolset.add(mcp_tool)

print("MCP tool configured successfully")


# Create agent with MCP tool and process agent run
with agents_client:

    # Create a new agent
    print("Creating agent...")
    try:
        agent = agents_client.create_agent(
            model=model_deployment,
            name="mcp-tool-discovery-agent",
            instructions="""
            You have access to an MCP server for client management. 
            Please list all the available tools/functions that you can call from this MCP server.
            For each tool, provide:
            1. The tool name
            2. A description of what it does
            3. Any parameters it accepts
            
            Be comprehensive and list ALL available tools from the MCP server.
            """
        )
        print(f"Created agent successfully, ID: {agent.id}")
    except Exception as agent_error:
        print(f"Error creating agent: {agent_error}")
        exit(1)
    

    # Log info
    print(f"Created agent, ID: {agent.id}")
    print(f"MCP Server: {mcp_tool.server_label} at {mcp_tool.server_url}")

    # Create thread for communication
    thread = agents_client.threads.create()
    print(f"Created thread, ID: {thread.id}")
    

    # Create a message on the thread asking about available tools
    message = agents_client.messages.create(
        thread_id=thread.id,
        role="user",
        content="What are all the available tools/functions I can use from the MCP server? Please list each tool with its name, description, and parameters.",
    )
    print(f"Created message, ID: {message.id}")
    

    # Create and process agent run in thread with MCP tools
    print("Creating and processing agent run...")
    try:
        run = agents_client.runs.create_and_process(thread_id=thread.id, agent_id=agent.id, toolset=toolset)
        print(f"Created run, ID: {run.id}")
        
        # Check run status
        print(f"Run completed with status: {run.status}")
        if run.status == "failed":
            print(f"Run failed: {run.last_error}")

        # Display run steps and tool calls
        run_steps = agents_client.run_steps.list(thread_id=thread.id, run_id=run.id)
        for step in run_steps:
            print(f"Step {step['id']} status: {step['status']}")

            # Check if there are tool calls in the step details
            step_details = step.get("step_details", {})
            tool_calls = step_details.get("tool_calls", [])

            if tool_calls:
                # Display the MCP tool call details
                print("  MCP Tool calls:")
                for call in tool_calls:
                    print(f"    Tool Call ID: {call.get('id')}")
                    print(f"    Type: {call.get('type')}")
                    print(f"    Function: {call.get('function', {}).get('name', 'N/A')}")
                    if 'function' in call and 'arguments' in call['function']:
                        print(f"    Arguments: {call['function']['arguments']}")
                    if 'output' in call:
                        print(f"    Output: {call['output']}")

            print()  # add an extra newline between steps

        # Fetch and log all messages
        messages = agents_client.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
        print("\nConversation:")
        print("-" * 50)
        for msg in messages:
            if msg.text_messages:
                last_text = msg.text_messages[-1]
                print(f"{msg.role.upper()}: {last_text.text.value}")
                print("-" * 50)

    except Exception as e:
        print(f"Error during agent run: {e}")
        print("Make sure your MCP server is accessible and your credentials are properly configured.")

    # Clean-up and delete the agent once the run is finished.
    try:
        agents_client.delete_agent(agent.id)
        print("Deleted agent")
    except Exception as cleanup_error:
        print(f"Warning: Could not delete agent: {cleanup_error}")
