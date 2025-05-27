import openai
import os
import json
import time
import sys
import asyncio # Required for async operations
from dotenv import load_dotenv

# Import the MCPClient class
from mcp_client import MCPClient

# Load environment variables
load_dotenv()

# Import tool definitions from tools_schema
from tools_schema import TOOLS_SCHEMA

# Configure OpenAI API connection
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:8000/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "NA")
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "Llama-3.2-8B-Instruct-Q4_K_M")
MCP_URL = os.getenv("MCP_URL", "http://localhost:8000/mcp")

print(f"Using OpenAI API at: {OPENAI_BASE_URL}")
print(f"Using MCP at: {MCP_URL}")

# Initialize OpenAI client
client = openai.OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
)

# Initialize MCP client with the URL
mcp_client = MCPClient()

async def execute_tool_calls(tool_calls):
    """Execute tool calls requested by the LLM (now asynchronous)"""
    tool_results = []
    
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_args = {}
        
        if tool_call.function.arguments:
            try:
                function_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError as e:
                print(f"Error parsing arguments for {function_name}: {e}", file=sys.stderr)
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps({"error": f"Invalid arguments: {e}"})
                })
                continue
        
        print(f"[CLI] Executing tool: {function_name} with args: {function_args}")
        
        if function_name == "get_random_question":
            result = await mcp_client.random_question()
        elif function_name == "get_question_and_answer":
            result = await mcp_client.search_question(function_args.get("text", ""))
        else:
            print(f"[CLI] Unknown tool: {function_name}", file=sys.stderr)
            result = {"error": f"Unknown tool: {function_name}"}
        
        tool_results.append({
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": function_name,
            "content": json.dumps(result) 
        })
        print(f"[CLI] Tool {function_name} result: {result}")
    
    return tool_results

async def amain(): 
    messages = [
        {"role": "system", "content": "You are an AI assistant helping users prepare for a tech certification. " +
                                     "When a user asks for a practice question, use the 'get_random_question' tool. " +
                                     "When a user asks a specific question, use the 'get_question_and_answer' tool to find relevant information. " +
                                     "If you use 'get_random_question', present ONLY the question to the user first. " +
                                     "Then, in subsequent turns, you can discuss the answer if the user asks or if it feels natural. " +
                                     "If you use 'get_question_and_answer', use the retrieved information to answer the user's question comprehensively."}
    ]
    
    print("\nLF Certification Exam Preparation Assistant (Async with Stdio MCP)")
    print("Type 'quit' or 'exit' to end the conversation")
    
    print("[CLI] Initializing MCP Client...")
    
    while True:
        try:
            user_input = await asyncio.to_thread(input, "\nUser: ") 
            if user_input.lower() in ["quit", "exit"]:
                print("Ending conversation")
                break
            
            messages.append({"role": "user", "content": user_input})
            
            print("Assistant: ", end="", flush=True)
            start_time = time.time()
            
            response_stream = client.chat.completions.create(
                model=MODEL_NAME, 
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                stream=True
            )
            
            collected_content = ""
            collected_tool_calls = [] 
            
            for chunk in response_stream:
                # Check if chunk has choices before accessing
                if not chunk.choices:
                    continue
                    
                delta = chunk.choices[0].delta
                if delta.content:
                    print(delta.content, end="", flush=True)
                    collected_content += delta.content  
                if delta.tool_calls:
                    for tc_chunk in delta.tool_calls:
                        if tc_chunk.index >= len(collected_tool_calls):
                            collected_tool_calls.append(tc_chunk) 
                        else:
                            existing_tc = collected_tool_calls[tc_chunk.index]
                            if tc_chunk.function and tc_chunk.function.arguments:
                                if existing_tc.function.arguments is None:
                                    existing_tc.function.arguments = tc_chunk.function.arguments
                                else:
                                    existing_tc.function.arguments += tc_chunk.function.arguments
            print() 

            assistant_message_for_history = {"role": "assistant", "content": collected_content}
            
            if collected_tool_calls:
                tool_call_objects_for_execution = [] 
                tool_call_dicts_for_history = [] 

                for tc_from_stream in collected_tool_calls:
                    tool_call_objects_for_execution.append(tc_from_stream) 
                    
                    tool_call_dicts_for_history.append({
                        "id": tc_from_stream.id,
                        "type": "function", 
                        "function": {
                            "name": tc_from_stream.function.name,
                            "arguments": tc_from_stream.function.arguments or "{}" 
                        }
                    })
                
                assistant_message_for_history["tool_calls"] = tool_call_dicts_for_history
                messages.append(assistant_message_for_history)

                tool_results = await execute_tool_calls(tool_call_objects_for_execution)
                
                for res in tool_results:
                    messages.append(res) 

                print("\nAssistant (after tools): ", end="", flush=True)
                follow_up_response_stream = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    stream=True
                )
                follow_up_content = ""
                for chunk in follow_up_response_stream:
                    # Check if chunk has choices before accessing
                    if not chunk.choices:
                        continue
                    if chunk.choices[0].delta.content:
                        print(chunk.choices[0].delta.content, end="", flush=True)
                        follow_up_content += chunk.choices[0].delta.content
                print() 
                messages.append({"role": "assistant", "content": follow_up_content})
            else:
                messages.append(assistant_message_for_history)
            
            print(f"\n[Processing time: {time.time() - start_time:.2f} seconds]")
            
        except KeyboardInterrupt:
            print("\nEnding conversation")
            break
        except Exception as e:
            print(f"\nAn unexpected error occurred in the main loop: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        print("\nExited by user.") 