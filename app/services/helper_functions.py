import os
import sys
import json
import pandas as pd
import pdfplumber
from docx import Document
from typing import List
from langchain_ollama import ChatOllama

# --- Path Optimization ---
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.abspath(os.path.join(_CURRENT_DIR, "..", ".."))

if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from services.config import ROOT_DIR, APP_DIR

MODEL_NAME = "gpt-oss:120b-cloud"

llm = ChatOllama(
    model=MODEL_NAME,
    temperature=0,
)


CAPTION_PROMPT = """You are an intelligent document understanding assistant for a Smart File System.

Your goal is to generate high-quality metadata for file discovery, preview, and semantic search.

Return ONLY valid JSON with:
- title (string)
- caption (string)

Guidelines:

TITLE:
- Be short, specific, and human-readable
- Include document type if possible (e.g., "Resume - John Doe", "Invoice - AWS Nov 2025")

CAPTION:
- 1–2 lines MAX
- Clearly explain:
  1. What the document is
  2. Key purpose/content
  3. Important entities (person, company, tech, dataset, etc.)
- Make it useful for:
  - search ranking
  - UI preview cards
  - semantic understanding

QUALITY RULES:
- Do NOT repeat the title in caption
- Avoid generic phrases like "This document contains..."
- Use natural, informative language
- Prefer clarity over verbosity
- If content is partial, infer intelligently

OUTPUT:
- Strict JSON only (no markdown, no explanation)
"""


def caption_file_content(document_text: str):
    messages = [
        ("system", CAPTION_PROMPT),
        ("human", f"DOCUMENT CONTENT:\n{document_text}")
    ]

    response = llm.invoke(messages)
    content = response.content.strip()

    try:
        parsed = json.loads(content)
    except:
        print("⚠️ JSON parsing failed. Attempting cleanup...")

        try:
            # Try to extract JSON substring
            start = content.find("{")
            end = content.rfind("}") + 1
            parsed = json.loads(content[start:end])
        except:
            parsed = {
                "title": "",
                "caption": content[:300]
            }

    return parsed


def describe_file(filepath: str):
    ext = os.path.splitext(filepath)[1].lower()
    content = ""

    try:
        if ext == ".pdf":
            with pdfplumber.open(filepath) as pdf:
                content = "\n".join(
                    page.extract_text() or "" for page in pdf.pages
                )

        elif ext == ".docx":
            doc = Document(filepath)
            content = "\n".join(p.text for p in doc.paragraphs)

        elif ext == ".txt":
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

        elif ext == ".csv":
            df = pd.read_csv(filepath, nrows=10)
            content = f"Columns: {', '.join(df.columns)}"

        else:
            print(f"❌ Unsupported file: {filepath}")
            return None

    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")
        return None

    # 🔥 Token-safe trimming
    words = content.split()
    return " ".join(words[:1200])



def generate_reasoning(query: str, file_path: str, file_type: str, pages_content: List[str]) -> str:
    # 🔹 Limit content to prevent context dilution
    pages_content = pages_content[:8] # Increased slightly as Gemma 3 handles context better

    formatted_content = ""
    for i, content in enumerate(pages_content, start=1):
        formatted_content += f"[[PAGE {i}]]: {content.strip()}\n\n"

    # OPTIMIZED PROMPT FOR GEMMA 3
    prompt = f"""<start_of_turn>user
    You are a precise Document Analyst. Your task is to prove the relevance of a document to a query using direct page references.

    QUERY: "{query}"
    FILE TYPE: {file_type}

    DOCUMENT CONTENT:
    {formatted_content}

    INSTRUCTIONS:
    1. Identify the specific sections that answer the query.
    2. Start your response with: "This document is relevant because..."
    3. For every claim, you MUST cite the page using the format: "on page X, it mentions..."
    4. Be strictly factual. Do not summarize the whole document; only the parts relevant to the query.
    5. Keep the total output under 4 sentences.

    OUTPUT EXAMPLE:
    This document is relevant because on page 1 it defines the project scope, and on page 8 it illustrates the system architecture diagram including the data pipeline.<end_of_turn>
    <start_of_turn>model
    """
    
    response = llm.invoke(prompt)
    return response.content.strip()




if __name__ == "__main__":
    query = "pipeline of stock watchlist assistant?"
    file_path = "app/data/documents/CA3-25070149025.pdf"
    file_type = "pdf"
    pages_content = [
        "AI in Fintech | SIT MTech AI/ML 2025–26\n4. Architecture\n4.1 System Architecture Diagram\nThe architecture diagram below shows the two-path design:\nFigure 1: End-to-end pipeline for explainable stock signal generation combining technical indicators and\nnews sentiment, served via a Flask dashboard and API.\n4.2 Two-Path Design\nThis application runs two completely independent data flows per ticker simultaneously:\nPath Trigger What It Does\nDaily Digest User clicks Run Analysis Full pipeline: price → news → FinBERT → ESF\n(once/day) → Groq. Result cached in localStorage by ticker\n+ IST date.\nLive Block Automatic every 30 seconds /api/quickprice/<ticker>: yfinance + pandas-ta\nonly. No LLM, no news. RSI, MACD, BB,\nVolume update in-place.\nPage 8",
        "AI in Fintech | SIT MTech AI/ML 2025–26\nA Project Report on\nStock Watchlist Assistant with Explainable Signal Fusion for Retail Investors\nField Value\nSubject AI in Fintech\nProgramme MTech AI/ML\nInstitution Symbiosis Institute of Technology, Pune\nAcademic Year 2025-26\nGitHub https://github.com/tp-0604/stock-watchlist\nFinBERT Model huggingface.co/tahp0604/finbert-sentfin\nThis document is a combined project report and application reference guide. It covers the\nmotivation, technical design, complete setup instructions, and usage guide for running the stock\nwatchlist application on any machine.\nSubmitted by\nTaher Poonawala 25070149025\nSubmitted To:\nDr. Anupkumar M Bongale\nPage 1",
        "or ignore it. The LLM's only role is language generation, not signal reasoning.\n3.5 LLM Digest Generation\nA single Groq API call (LLaMA 3.3-70B) per stock per day generates the plain-English digest.\nThe prompt passes the pre-compute fusion_narrative and the user's goal, and constrains the\nLLM to, for example:\n""",
        "The problem does not stem from a lack of data. Stock price data, technical indicators, and\nfinancial news are all available at no cost. The issue is synthesis: no user-friendly tool exists\nthat takes all these signals, settles conflicts between them, and then explains the outcome in\nclear English linked to a particular personal objective.\n1.2 Limitations of Existing Tools\n• Traditional charting tools (TradingView, Zerodha Kite) display RSI, MACD, and\nBollinger Bands visually. The user must interpret these signals themselves — requiring\nfinancial literacy that most retail investors do not have.\n• LLM-based research systems (TradingAgents, MarketSenseAI, FinAgent, Ploutos) are\ndesigned for institutional or algorithmic use. They require significant API costs, target",
        "depend on unverified tips. By providing institutional-grade multi-signal analysis at almost no\ncost, through the use of free API tiers, open-source models, and a fine-tuned domain-adapted\nFinBERT, this application proves that principled reproducible explainable AI can be made\navailable to those who are most in need of it. The design of the architecture also has a bearing\non regulatory compliance. SEBI and RBI are ramping up their scrutiny of AI-generated\nfinancial advice. The ESF architecture is capable of recording everything: each conflict\ndetection, fusion score, and signal classification is a logged Python object with a deterministic\nand traceable computation path.\nPage 13",
        "• The system does not place orders or connect to any brokerage.\n6. Impact Overview Statement\n6.1 Research Contribution: Explainable Signal Fusion\nA systematic search across Google Scholar, arXiv, Semantic Scholar, ACM, IEEE, and\nSpringer return zero results for the term 'Explainable Signal Fusion' as of April 2026. The\npattern is absent from all prior systems reviewed.\nThe key architectural distinction is where the fusion decision is made:\nAspect Existing Systems This project (ESF)\nSignal fusion Implicit inside LLM or neural net Explicit Python code\nConflict detection Not surfaced to user Detected before LLM, logged to DB\nLLM role Fuses + explains simultaneously Narrates only\nTarget user Algo traders / researchers Retail investors",
        "sentiment_analyzer.py Fine-tuned FinBERT batched inference\nfusion/\nsignal_fusion.py ESF: weighted fusion + conflict detection\nllm/\ndigest_generator.py Groq prompt construction + API call\nscripts/scheduler.py APScheduler daily job (optional)\ntests/ Unit tests (no API keys needed)\nrequirements.txt\n.env.example Copy to .env and add GROQ_API_KEY\nsetup.sh / setup.bat One-command setup\nrun.sh / run.bat One-command run\nDockerfile\ndocker-compose.yml\n4.4 API Endpoints\nMethod Endpoint Purpose Called By\nGET / Render main page Browser on load\nPOST /watchlist/add Add ticker + goal app.js addTicker()\nDELETE /watchlist/remove/<ticker> Remove ticker app.js\nremoveTicker()\nGET /analyse/<ticker> Full pipeline - returns app.js fetchDigest()\nDigestCard JSON\nPage 9",
        "F1 on Indian financial news 0.873 vs ~0.76 ProsusAI/finbert baseline\nGoogle Scholar hits for ESF 0 Term confirmed novel April 2026\nGroq API calls per stock/day 1 vs 5–10 GPT-4 calls in competing systems\nParallel analysis (3 stocks) ~7 seconds vs ~21 seconds sequential\nAPI cost to operate daily Free Groq free tier + yfinance (no key)\nSupported exchanges NSE, BSE, US Via Yahoo Finance search API\n6.4 Closing Statement\nThis application proposal seeks to solve a very real and rapidly increasing problem in the Indian\nretail investment area. India has opened around 30 million new demat accounts in the year\n2023-24. Most of those investors do not have any method to evaluate stock signals and merely\ndepend on unverified tips. By providing institutional-grade multi-signal analysis at almost no",
        "cards, existing cards are preserved.\n5.3 Reading a Card\nEach card has 3 sections:\n5.3.1 Header\nDisplays company name, ticker symbol, and a signal badge: Signals in agreement or\nConflicting signals (TA and sentiment pointing in opposite directions).\n5.3.2 Live Block (updates every 30 seconds)\nField What It Shows How to Read\nPrice + Change % Current close vs previous Green = up today, Red = down today\nclose\nRSI (14) Momentum indicator 0–100 < 30 = oversold (buy signal), > 70 =\noverbought (sell signal), 30–70 = neutral\nMACD / Signal / Hist Trend momentum Histogram positive = bullish momentum,\nnegative = bearish\nBB Price range bands Price above upper = overbought; below\nUpper/Mid/Lower lower = oversold\nVolume / Vol Avg Today vs 20-day average Volume spike triangle = unusual activity\n20d"
    ]
    print(generate_reasoning(query, file_path, file_type, pages_content))
