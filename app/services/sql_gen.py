import re
import pandas as pd
import ollama

MODEL_NAME = "gemma3:1b"


def clean_sql(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```sql\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def sql_query_generator(user_input: str, csv_path: str, table_name: str) -> str:
    df = pd.read_csv(csv_path)

    columns = df.columns.tolist()
    sample_rows = df.head(5).to_string(index=False)

    system_prompt = f"""
You are a STRICT SQL query generator.

You MUST follow ALL rules below.

GENERAL RULES:
- Output EXACTLY ONE SQL query
- Output ONLY raw SQL (no markdown, no explanation)
- Use ONLY the table and columns provided
- Column names are CASE-SENSITIVE
- ALWAYS wrap column names with spaces in double quotes
- NEVER invent columns
- NEVER invent joins
- Assume a SINGLE table only

AGGREGATION RULES:
- If the question asks for total / sum → use SUM
- If it asks for average → use AVG
- NEVER return string literals instead of calculations
- If GROUP BY is used, all non-aggregated columns MUST be in GROUP BY

FILTER RULES:
- Use WHERE for filtering
- Use correct column types:
  - Month is NUMERIC (e.g., 10 for October)
  - Year is NUMERIC
  - Discount Applied is 'Yes' / 'No'
  - Returned Status is 'Returned' / 'Kept'

FAILURE HANDLING:
- If the request cannot be satisfied using available columns, return EXACTLY:
  SELECT 'ERROR: missing or unclear column' AS error;

TABLE:
{table_name}

COLUMNS:
{columns}

SAMPLE ROWS (for value formats only):
{sample_rows}

------------------------------------------------
FEW-SHOT CORRECTION EXAMPLES (IMPORTANT)
------------------------------------------------

User request:
Get total revenue for customers who used CARD.

SQL:
SELECT SUM("Revenue") AS TotalRevenue
FROM {table_name}
WHERE "Payment mode" = 'CARD';

------------------------------------------------

User request:
Find customers who received any discount.

SQL:
SELECT "Customer ID"
FROM {table_name}
WHERE "Discount Applied" = 'Yes';

------------------------------------------------

User request:
List products that were returned.

SQL:
SELECT "Product bought"
FROM {table_name}
WHERE "Returned Status" = 'Returned';

------------------------------------------------

User request:
Get total discount amount for the month of October.

SQL:
SELECT SUM("Discount Amount") AS TotalDiscount
FROM {table_name}
WHERE "Month" = 10;

------------------------------------------------

User request:
Find customer IDs who bought products of size M.

SQL:
SELECT "Customer ID"
FROM {table_name}
WHERE "Size" = 'M';

------------------------------------------------

User request:
Find patients with blood type A+.

SQL:
SELECT *
FROM {table_name}
WHERE "Blood Type" = 'A+';

------------------------------------------------

User request:
Get total billing amount for each insurance provider.

SQL:
SELECT "Insurance Provider", SUM("Billing Amount") AS TotalBilling
FROM {table_name}
GROUP BY "Insurance Provider";

------------------------------------------------

User request:
List patients treated by Matthew Smith.

SQL:
SELECT *
FROM {table_name}
WHERE "Doctor" = 'Matthew Smith';

------------------------------------------------
END OF EXAMPLES
------------------------------------------------

Now generate the SQL query for the user request below.
""".strip()


    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input.strip()},
    ]

    response = ollama.chat(
        model=MODEL_NAME,
        messages=messages,
    )

    output = clean_sql(response["message"]["content"])

    return columns, output


# sample = [
#     "Find total revenue for female customers who paid using CARD.",
#     "how average discount amount by category for products that were returned.",
#     "Find patients older than 50 admitted under Emergency."
# ]