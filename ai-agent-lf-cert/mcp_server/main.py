import json
import os
import random
import sys
import numpy as np
from typing import Dict, List, Any
import requests
from fastmcp import FastMCP
import openai
from dotenv import load_dotenv

mcp = FastMCP("LF Cert Prep Tools")

QUESTIONS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "cka_qa.json")
QUESTIONS_DATA = []
EMBEDDINGS_CACHE = {}
QUESTION_EMBEDDINGS = None
QUESTION_IDS = []


load_dotenv()

EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "http://localhost:8080/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text-v1.5")
EMBEDDING_API_KEY = os.getenv("OPENAI_API_KEY", "NA")

client = openai.OpenAI(
    api_key=EMBEDDING_API_KEY,
    base_url=EMBEDDING_API_URL
)


def get_embedding(text: str) -> List[float]:
    """Get embedding for text using local embedding API server."""
    try:
        resp = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        print(f"{text}\n:{len(resp.data[0].embedding)}")
        return resp.data[0].embedding
        
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def load_questions():
    global QUESTIONS_DATA, QUESTION_EMBEDDINGS, QUESTION_IDS
    try:
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            QUESTIONS_DATA = json.load(f)
            
        # Generate embeddings for all questions
        print(f"Generating embeddings for {len(QUESTIONS_DATA)} questions...", file=sys.stderr)
        embeddings = []
        question_ids = []
        
        for qa_pair in QUESTIONS_DATA:
            question_text = qa_pair.get("question", "")
            question_id = qa_pair.get("id")
            embedding = get_embedding(question_text)
            if embedding:
                embeddings.append(embedding)
                question_ids.append(question_id)
        
        if embeddings:
            QUESTION_EMBEDDINGS = np.array(embeddings)
            QUESTION_IDS = question_ids
            print(f"Successfully generated embeddings with shape {QUESTION_EMBEDDINGS.shape}", file=sys.stderr)
        else:
            print("Failed to generate any embeddings", file=sys.stderr)
            
    except FileNotFoundError:
        print(f"Error: {QUESTIONS_FILE} not found. Make sure the data file exists.", file=sys.stderr)
        QUESTIONS_DATA = []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {QUESTIONS_FILE}.", file=sys.stderr)
        QUESTIONS_DATA = []

@mcp.tool()
def get_random_question() -> dict:
    """Selects a random question from a list. It returns both the question and the answer."""
    if not QUESTIONS_DATA:
        return {"error": "No questions loaded. Check data file."}
    selected = random.choice(QUESTIONS_DATA)
    return selected # Returns a dict like {"id": ..., "question": ..., "answer": ...}

@mcp.tool()
def get_question_and_answer(text: str) -> dict:
    """Searches an input text from the database for a corresponding question and answer using semantic similarity."""
    if not QUESTIONS_DATA or QUESTION_EMBEDDINGS is None:
        return {"error": "No questions or embeddings loaded. Check data file."}
    
    # Get embedding for the query text
    query_embedding = get_embedding(text)
    if not query_embedding:
        return {"error": "Failed to generate embedding for the query"}
    
    # Calculate similarity with all question embeddings
    query_embedding_np = np.array(query_embedding)
    similarities = np.array([cosine_similarity(query_embedding_np, q_emb) for q_emb in QUESTION_EMBEDDINGS])
    
    # Find the most similar question
    most_similar_idx = np.argmax(similarities)
    similarity_score = similarities[most_similar_idx]
    question_id = QUESTION_IDS[most_similar_idx]
    
    # Get the corresponding QA pair
    for qa_pair in QUESTIONS_DATA:
        if qa_pair.get("id") == question_id:
            result = qa_pair.copy()
            result["similarity_score"] = float(similarity_score)
            return result
            
    return {"error": f"No semantically similar question found for '{text}'"}

if __name__ == "__main__":
    load_questions()
    if not QUESTIONS_DATA:
        print("MCP server exiting as no questions could be loaded.", file=sys.stderr)
        sys.exit(1)
    print(f"MCP Server started. Loaded {len(QUESTIONS_DATA)} questions from {QUESTIONS_FILE}.", file=sys.stderr)
    print("Waiting for tool calls via streamable-http...", file=sys.stderr)
    mcp.run(transport="streamable-http") 