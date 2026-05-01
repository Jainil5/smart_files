import os
import sys
import requests
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain.tools import tool

# --- Path Optimization ---
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.dirname(_CURRENT_DIR)
_ROOT_DIR = os.path.dirname(_APP_DIR)

if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

from services.config import ROOT_DIR, SALES_CSV, HEALTH_CSV
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
    """Perform QnA over internal documents using RAG. Answer to questions of user using the documents. Add sources as link with response."""
    try:
        response = rag_qna(query)
        # print(response)
        return response

    except Exception as e:
        return f"Error in RAG: {str(e)}"

#RESPONSE:
# {'response': '**Pipeline**\n\n1. **Data acquisition** –\u202f`price_fetcher.py` pulls OHLCV data (yfinance) and technical indicators (pandas‑ta); `news_fetcher.py` pulls ticker‑specific headlines (yfinance.news).  \n\n2. **Technical signal generation** –\u202f`signals/technical_signals.py` scores the indicators (RSI, MACD, Bollinger Bands, volume, etc.).  \n\n3. **Sentiment analysis** –\u202f`sentiment_analyzer.py` runs the fine‑tuned FinBERT model on the fetched news in batches.  \n\n4. **Explainable Signal Fusion (ESF)** –\u202f`fusion/signal_fusion.py` combines the technical scores and FinBERT sentiment using weighted fusion, detects conflicts, and produces a `FusionResult`.  \n\n5. **Digest generation** –\u202f`llm/digest_generator.py` builds a Groq prompt from the fused result and calls the Groq LLM to create a human‑readable `DigestCard`.  \n\n6. **Orchestration** –\u202f`pipeline.py` coordinates the whole flow (price\u202f→\u202fnews\u202f→\u202fFinBERT\u202f→\u202fESF\u202f→\u202fGroq) for the **Daily Digest** (run once per day, cached in localStorage).  \n\n7. **Live block** –\u202fEvery 30\u202fseconds the API `/api/quickprice/<ticker>` (Flask) refreshes only the price data and technical indicators (no news or LLM) for real‑time UI updates.', 'file_name': 'CA3-25070149025.pdf', 'file_type': '.pdf', 'hosted_link': None}

@tool
def search_tool(query: str):
    """Search relevant files/documents for discovery."""
    try:
        response = suggest_files(query)
        
        # if response == [] or response == {}:
        #     return "No relevant files found."

        # output = f"## 📂 Relevant Files\n\n"

        # for i, doc in enumerate(response, 1):
        #     print(doc)
        #     output += f"### {i}. {doc.get('file_name', 'Unknown')}\n\n"

        #     if doc.get("file_type"):
        #         output += f"Type: {doc['file_type']}\n"

        #     if doc.get("hosted_link"):
        #         output += f"<a href='{doc['hosted_link']}'>{doc['hosted_link']}</a>\n"

        #     reasons = doc.get("response", "")
        #     if reasons:
        #         output += "\nWhy Relevant:\n"
        #         for r in reasons:
        #             if r.strip():
        #                 output += f"- {r.strip()}\n"

        #     output += "\n"

        return response

    except Exception as e:
        return f"Error in search: {str(e)}"


# Response:
# [{'response': 'This document is relevant because on page\u202f1, it mentions the “Stock Watchlist Assistant” project and its purpose; on page\u202f2, it provides the commands to set up and run the application; and on page\u202f4, it outlines the technical pipeline and API endpoints for analysing tickers.', 'file_name': 'CA3-25070149025.pdf', 'file_type': 'pdf', 'hosted_link': None}
# {'response': 'This document is relevant because on page 1, it mentions tracking IT assets and creating a software license tracker, and on page 2, it mentions email composition and market research, neither of which relate to a stock watchlist assistant.', 'file_name': 'gemini-for-google-workspace-prompting-guide-101.pdf', 'file_type': 'pdf', 'hosted_link': None}
# {'response': 'This document is not relevant because on page\u202f1 it mentions FitxHealth, a coffee‑shop chatbot, AI‑based website controls, and various programming skills, none of which relate to a stock watchlist assistant.', 'file_name': 'jainil-resume.pdf', 'file_type': 'pdf', 'hosted_link': None}
# {'response': 'This document is relevant because on page\u202f1, it lists several Google\u202fDrive file URLs, which could include the stock watchlist assistant file you are seeking; on page\u202f1, it provides direct links to files that can be opened to locate the desired document.', 'file_name': 'test_links.py', 'file_type': 'text', 'hosted_link': 'https://smartfiless3.s3.amazonaws.com/test_links.py?response-content-type=text%2Fx-python&response-content-disposition=inline%3B%20filename%3D%22test_links.py%22&AWSAccessKeyId=AKIAQ47TESKDDHQGGQKZ&Signature=ULPPeTcay1Vvix%2FAN1j0TX96ExA%3D&Expires=1777295783'}]

@tool
def generate_sql_sales(text: str):
    """Generate SQL query for the clothing sales dataset."""
    try:
        _, response = sql_query_generator(
            text,
            csv_path=SALES_CSV,
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
            csv_path=HEALTH_CSV,
            table_name="Health"
        )

        return f"Generated SQL Query\n\n{response}"

    except Exception as e:
        return f"SQL Error: {str(e)}"


agent_prompt = """
You are a HIGH-PRECISION tool routing assistant.

Your role:
1. Understand the user query and analyze intent.
2. Select exactly ONE correct tool.
3. Transform tool output into CLEAN, STRUCTURED MARKDOWN.
4. Return ONLY the final formatted response.

----------------------------------------
QUERY ANALYSIS & TOOL SELECTION
----------------------------------------

Before selecting a tool, identify the intent:

1. **Discovery Intent**: Use `search_tool`.
   - Trigger: User wants to "find", "show", "locate", or "get" a file/code.
   - Example: "Find me the resume", "Get the code for DB connection".

2. **Information Intent**: Use `rag_tool`.
   - Trigger: User asks a specific question *about* document content.
   - Example: "How does the pipeline work?", "Explain the technical scores".

3. **Data/Weather Intent**: Use SQL or Weather tools accordingly.

----------------------------------------
GLOBAL STYLING & UI RULES
----------------------------------------
The following rules apply to ALL tool outputs and responses:

- **Bolding**: Always bold file names, document titles, or major entities in **[File Name]** or **Entity** format.
- **Links**: Always place links on their own line. Ensure they are clickable (Markdown format).
- **Line Breaks**: Use double line breaks between paragraphs and sections for maximum readability in the UI.
- **Horizontal Rules**: Use `---` to separate distinct entities (like multiple file results) or to separate the answer from the source section.
- **Structure**: Use bullet points for lists and numbered lists for steps.
- **Direct Start**: Never start with "Here is your answer" or "I found...". Start IMMEDIATELY with the most important content.

----------------------------------------
TRANSFORMATION & FORMATTING RULES
----------------------------------------

### 1. For Search Results (File Discovery)
- DO NOT add a "Relevant Documents" header.
- Start directly with the first file name in bold.
- Format:
  **[File Name]**
  **Reason:** [Reason] (OMIT if no reason is provided)
  **Source:** [File Name]
  **Link:** [Link or "Not Available"]
- Separator: Use `---` between files.

### 2. For RAG Answers (Information Retrieval)
- DO NOT add an "Answer" header.
- Start directly with the answer text using bolding and bullet points as needed.
- Separator: Use `---` after the answer.
- **Source Section**:
  **Source:** [File Name]  
  **Link:** [Link or "Not Available"]

### 3. For SQL & Other Tools
- Start directly with the results (e.g., code block for SQL, structured list for data).
- Ensure all technical output is wrapped in proper Markdown blocks (e.g., ```sql).

----------------------------------------
STRICT BEHAVIOR RULES
----------------------------------------
- Analyze intent FIRST to pick the right tool.
- DO NOT add any meta-talk, intro text, or conversational filler.
- Start your response IMMEDIATELY with formatted content.
- Optimize every response for a premium, structured UI display.
- Return ONLY the Markdown formatted results.

----------------------------------------
FAILSAFE
----------------------------------------
If uncertain → Ask user for context. DO NOT use any tool.
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
        # "Find patients older than 50 with blood group A+ admitted under Emergency.",
        # "What's the weather in Mumbai?",
        # "what is the pipeline of stock watchlist assistant?",
        # "What is tech stack of ai sales analyst"
    ]

    for i, query in enumerate(test_queries, start=1):
        print("--------------------------------------------------")
        print(f"[{i}] Q: {query}")
        result = bot(query)
        print("A:\n", result)