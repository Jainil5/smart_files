from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain.tools import tool
import requests

from services.main_rag import rag_qna
from services.main_search import suggest_files
from services.sql_gen import sql_query_generator
from services.monitoring import start_run, log_agent_query, log_agent_response


llm = ChatOllama(
    model="gpt-oss:20b-cloud",
    temperature=0,
    top_p=0.9,
)


@tool
def get_weather(location: str):
    """Fetch current weather for a given city/location."""
    try:
        res = requests.get(f"https://wttr.in/{location}?format=j1", timeout=5).json()
        current = res["current_condition"][0]

        return (
            f"Weather Report\n\n"
            f"Location: {location}\n"
            f"Temperature: {current['temp_C']}°C\n"
            f"Condition: {current['weatherDesc'][0]['value']}\n"
            f"Humidity: {current['humidity']}%\n"
        )

    except Exception as e:
        return f"Error fetching weather: {str(e)}"


@tool
def rag_tool(query: str):
    """Perform QnA over internal documents using RAG."""
    try:
        res = rag_qna(query)

        output = "Answer\n\n"
        output += res.get("response", "No answer found") + "\n\n"

        if res.get("file_name"):
            output += "Source\n"
            output += f"{res['file_name']}\n\n"

        if res.get("hosted_link"):
            output += f"Link\n{res['hosted_link']}\n"

        return output.strip()

    except Exception as e:
        return f"Error in RAG: {str(e)}"


@tool
def search_tool(query: str):
    """Search relevant files/documents for discovery."""
    try:
        response = suggest_files(query)

        relevant_docs = []
        for doc in response:
            reasoning = doc.get("reasoning", "").lower()
            if "not relevant" not in reasoning:
                relevant_docs.append(doc)

        if not relevant_docs:
            return "No relevant documents found."

        output = f"Relevant Documents\n\nTotal: {len(relevant_docs)}\n\n"

        for i, doc in enumerate(relevant_docs, 1):
            output += f"{i}. {doc.get('file_name', 'Unknown')}\n\n"

            if doc.get("file_type"):
                output += f"Type: {doc['file_type']}\n"

            if doc.get("file_path"):
                output += f"Path: {doc['file_path']}\n"

            if doc.get("hosted_link"):
                output += f"Link: {doc['hosted_link']}\n"

            reasons = doc.get("reasoning", "").split(".")[:2]
            if reasons:
                output += "\nWhy Relevant:\n"
                for r in reasons:
                    if r.strip():
                        output += f"- {r.strip()}\n"

            output += "\n"

        return output.strip()

    except Exception as e:
        return f"Error in search: {str(e)}"


@tool
def generate_sql_sales(text: str):
    """Generate SQL query for the clothing sales dataset."""
    try:
        _, response = sql_query_generator(
            text,
            csv_path="data/datasets/clothing_sales_combined.csv",
            table_name="Sales"
        )

        return f"Generated SQL Query\n\n{response}"

    except Exception as e:
        return f"SQL Error: {str(e)}"


@tool
def generate_sql_health(text: str):
    """Generate SQL query for the healthcare dataset."""
    try:
        _, response = sql_query_generator(
            text,
            csv_path="data/datasets/healthcare_dataset.csv",
            table_name="Health"
        )

        return f"Generated SQL Query\n\n{response}"

    except Exception as e:
        return f"SQL Error: {str(e)}"


agent_prompt = """
You are a HIGH-PRECISION tool routing assistant.

Your role is to:
- Understand the user query
- Select exactly one correct tool
- Return only the tool output

----------------------------------------
STRICT OUTPUT FORMAT RULES
----------------------------------------
- Output must be clean, structured, and readable
- Use proper spacing between sections
- Always include clear section headers where applicable
- Use line breaks between logical blocks
- Avoid cluttered or compressed text
- Keep alignment consistent
- Do not include unnecessary symbols or decorations

----------------------------------------
STRICT BEHAVIOR RULES
----------------------------------------
1. Do not explain reasoning
2. Do not add any text before or after output
3. Do not modify tool output meaning
4. Do not summarize tool output
5. Do not mention tools
6. Do not wrap output in code blocks
7. Always return final formatted output only

----------------------------------------
OUTPUT DECISION
----------------------------------------
- If tool is used → return fully formatted tool output
- If no tool applies → return short structured answer (max 2 lines)

----------------------------------------
TOOL SELECTION LOGIC
----------------------------------------
1. search_tool → file discovery
2. rag_tool → document-based answers
3. generate_sql_sales → sales queries
4. generate_sql_health → healthcare queries
5. get_weather → weather data

----------------------------------------
PRIORITY ORDER
----------------------------------------
1. SQL tools
2. rag_tool
3. search_tool
4. weather

----------------------------------------
FAILSAFE
----------------------------------------
If uncertain → use rag_tool
"""


agent = create_agent(
    llm,
    tools=[
        get_weather,
        rag_tool,
        search_tool,
        generate_sql_sales,
        generate_sql_health,
    ],
    system_prompt=agent_prompt,
)


def bot(user_input: str):
    with start_run("agent_interaction"):
        log_agent_query(user_input)
        
        response = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]}
        )
        
        res_content = response["messages"][-1].content
        log_agent_response(res_content)
        
        return res_content


if __name__ == "__main__":
    test_queries = [
        "Find me research paper on h2ogpt.",
        "Why was my leave application rejected?",
        "Find patients older than 50 with blood group A+ admitted under Emergency.",
        "What's the weather in Mumbai?",
    ]

    for i, query in enumerate(test_queries, start=1):
        print("--------------------------------------------------")
        print(f"[{i}] Q: {query}")
        result = bot(query)
        print("A:\n", result)