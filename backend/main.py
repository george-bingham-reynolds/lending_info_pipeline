"""
FastAPI backend wrapping the working BigQuery + Anthropic LLM pipeline.
Provides a /ask endpoint for natural-language questions about loan records.
"""
import os
import json
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.cloud import bigquery
import anthropic

# Load environment variables from .env file
load_dotenv()

# Import constants from pipeline_helpers (one level up)
import sys
sys.path.append('..')
from pipeline_helpers import BQ_DS

# Project configuration - reusing existing setup
PROJECT_ID = "lending-info-pipeline"
PIPELINE_END_TABLE_1 = "financial_statements"
PIPELINE_END_TABLE_2 = "appraisals"

# Build full table IDs for BQ queries
table_ids = [
    f"{PROJECT_ID}.{BQ_DS}.{PIPELINE_END_TABLE_1}",
    f"{PROJECT_ID}.{BQ_DS}.{PIPELINE_END_TABLE_2}"
]

# Initialize clients - GCP uses ADC automatically, Anthropic reads from env
bq_client = bigquery.Client(project=PROJECT_ID)
anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# FastAPI app setup
app = FastAPI(title="Lending Info Pipeline API")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === CORE PIPELINE FUNCTIONS (copied from llm_interaction.ipynb) ===

def pull_loan_records(loan_number: str, table_ids: list[str]) -> dict | None:
    """
    Looks up a loan's structured records across multiple BQ tables and merges
    them into a single nested JSON, keyed by table (doc type):
        {
          "loan_number": ...,
          "financial_statements": {
            "source_filename": ...,
            "fields": {"total_revenue": {"value": ..., "confidence": ...}, ...}
          },
          "appraisals": {
            "source_filename": ...,
            "fields": {"appraised_value": {...}, ...}
          }
        }
    Only returns None if the loan number isn't found in ANY of the tables —
    a miss in one table alone isn't fatal, since a question may only be
    answerable from a subset of doc types.
    """
    combined = {"loan_number": loan_number}
    found_any = False

    for table_id in table_ids:
        query = f"""
            SELECT *
            FROM `{table_id}`
            WHERE loan_number = @loan_number
            LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("loan_number", "STRING", loan_number)
            ]
        )
        result = bq_client.query(query, job_config=job_config).to_dataframe()

        if result.empty:
            continue  # this table has no record for this loan — not fatal, keep going

        found_any = True
        row = result.iloc[0].to_dict()

        identifier_cols = {"source_filename", "loan_number"}
        confidence_cols = {c for c in row if c.endswith("_confidence")}
        field_cols = {
            c for c in row
            if c not in identifier_cols and f"{c}_confidence" in confidence_cols
        }

        fields = {
            field: {"value": row[field], "confidence": row[f"{field}_confidence"]}
            for field in field_cols
        }

        table_name = table_id.split(".")[-1]  # e.g. "financial_statements"
        combined[table_name] = {
            "source_filename": row.get("source_filename"),
            "fields": fields,
        }

    return combined if found_any else None


def extract_loan_number(user_question: str) -> str | None:
    """
    Uses the LLM to identify the loan number referenced in a natural-language
    question. Returns the loan number string, or None if no loan number is
    mentioned. This is the simplest possible stand-in for semantic search —
    the user has to name the loan explicitly for now (matches the fallback
    plan: exact-identifier lookup now, true semantic search as a later upgrade).
    """
    system_prompt = (
        "Extract the loan number mentioned in the user's question. "
        "Loan numbers follow the format MTN-##### (e.g. MTN-10234). "
        "Return ONLY the loan number, exactly as written, with no other text. "
        "If no loan number is mentioned in the question, return exactly: NONE"
    )
 
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=50,
        system=system_prompt,
        messages=[{"role": "user", "content": user_question}],
    )
 
    result = response.content[0].text.strip()
    return None if result == "NONE" else result


def generate_grounded_answer(user_question: str, loan_context: dict) -> str:
    """
    Takes a user's natural-language question and the structured loan context
    (from pull_loan_record) and returns an LLM-generated answer grounded
    strictly in that context, with confidence flags surfaced.
    """
    context_str = json.dumps(loan_context, indent=2, default=str)
 
    system_prompt = (
        "You help answer questions about commercial real estate loans. "
        "You will be given structured context extracted from a loan's financial "
        "statement, including a confidence score (0-100) for each field. "
        "Always answer strictly using the values given in the context — "
        "never state a number that isn't present in the context. "
        "If the person asks about a field that isn't present in the context, "
        "respond: \"I can't see a value for that field, I'm sorry.\" "
        "When you do answer with a number, mention its confidence score. "
        "If the confidence score for a field is below 90, explicitly flag "
        "that the value should be manually verified against the source "
        "document before being relied on."
    )
 
    user_message = (
        f"{user_question}\n\n"
        f"Grounded context to answer the question:\n{context_str}"
    )
 
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
 
    return response.content[0].text


def answer_question(user_question: str, table_ids: list[str]) -> str:
    """
    Full parse-pull-inject-answer flow, driven entirely by a natural-language
    question:
      1. Extract the loan number from the question (LLM)
      2. Pull the structured record for that loan number (BQ)
      3. Generate a grounded answer using that record as context (LLM)
    """
    loan_number = extract_loan_number(user_question)
    if loan_number is None:
        return (
            "I couldn't find a loan number in your question. "
            "Could you include the loan number you're asking about?"
        )

    loan_data = pull_loan_records(loan_number, table_ids)
    if loan_data is None:
        return f"I don't have any records for loan number {loan_number}."

    return generate_grounded_answer(user_question, loan_data)


# === API MODELS ===

class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    answer: str


# === API ENDPOINTS ===

@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Lending Info Pipeline API is running"}


@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    """
    Accept a natural-language question about a loan and return a grounded answer.
    
    The question must reference a specific loan number (e.g., MTN-10234) to work.
    The answer will be based on structured data extracted from BigQuery tables.
    """
    answer = answer_question(request.question, table_ids)
    return AnswerResponse(answer=answer)
