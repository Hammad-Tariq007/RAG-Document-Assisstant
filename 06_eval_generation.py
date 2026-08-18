import os

import psycopg2
from anthropic import Anthropic
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

load_dotenv()

conn = psycopg2.connect(
    host="localhost", port=5433, dbname="ragdb",
    user="postgres", password="ragpass",
)
register_vector(conn)
cur = conn.cursor()
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

client = Anthropic(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api",
)


# ---- The real pipeline: retrieve + generate (same as 04_answer.py) ----
def rag_answer(question: str, top_k: int = 3) -> str:
    q_vector = embed_model.encode(question)
    cur.execute(
        "SELECT content FROM chunks ORDER BY embedding <=> %s LIMIT %s;",
        (q_vector, top_k),
    )
    chunks = [row[0] for row in cur.fetchall()]

    context = ""
    for i, chunk in enumerate(chunks):
        context += f"[Source {i + 1}] {chunk}\n\n"

    prompt = f"""Answer the question using ONLY the context below.
If the answer is not in the context, say "I don't know based on the provided documents."
After each claim, cite the source number in brackets, like [Source 1].

Context:
{context}
Question: {question}"""

    response = client.messages.create(
        model="anthropic/claude-haiku-4.5",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


# ---- The JUDGE: a second LLM call that grades the answer ----
def judge_answer(question: str, answer: str, expected: str) -> dict:
    judge_prompt = f"""You are a strict grader evaluating an AI assistant's answer.

Question: {question}

Expected correct answer (the key facts that must be present): {expected}

The AI assistant's actual answer: {answer}

Grade the answer on whether it correctly contains the expected key facts.
Respond with ONLY a JSON object (no markdown, no extra text) with these keys:
- "verdict": "PASS" if the answer correctly conveys the expected facts, "FAIL" otherwise
- "reason": a one-sentence explanation of your grade
"""
    response = client.messages.create(
        model="anthropic/claude-haiku-4.5",
        max_tokens=200,
        messages=[{"role": "user", "content": judge_prompt}],
    )
    raw = response.content[0].text
    # reuse the defensive JSON extraction from Stage C
    import json
    start, end = raw.find("{"), raw.rfind("}")
    return json.loads(raw[start:end + 1])


# ---- The eval dataset: question + the expected key facts ----
eval_set = [
    {"question": "What did Hammad build for the business development team?",
     "expected": "An AI-powered CRM for the BD team that tracks the lead lifecycle."},
    {"question": "Where did Hammad study?",
     "expected": "The University of the Punjab (PUCIT)."},
    {"question": "What was Hammad's final year project?",
     "expected": "Fitness Freaks, an AI fitness and diet app using Google Gemini."},
    {"question": "What is Hammad's favorite food?",
     "expected": "The documents do not contain this information; the answer should say it doesn't know."},
]


def evaluate_generation():
    passes = 0
    print(f"Evaluating generation on {len(eval_set)} questions:\n")

    for test in eval_set:
        answer = rag_answer(test["question"])
        result = judge_answer(test["question"], answer, test["expected"])

        if result["verdict"] == "PASS":
            passes += 1

        print(f"[{result['verdict']}] {test['question']}")
        print(f"        answer: {answer[:100].strip()}...")
        print(f"        judge:  {result['reason']}\n")

    score = passes / len(eval_set)
    print(f"Generation score: {passes}/{len(eval_set)} = {score:.0%}")
    return score


if __name__ == "__main__":
    evaluate_generation()
    cur.close()
    conn.close()