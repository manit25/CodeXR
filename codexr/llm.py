import os, json, asyncio
from typing import Dict, Any, List
import google.generativeai as genai
import requests
from dotenv import load_dotenv

from codexr.schema import Answer, Subtask, DocRef  # local imports

# Always load .env before configuring Gemini
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
SERPER_KEY = os.getenv("SERPER_API_KEY")

_VERBOSITY = {
    "concise": "Provide a very short, bullet-point summary with minimal explanation. Omit detailed explanations for code snippets.",
    "normal": "Provide a one-paragraph summary per subtask, a short explanation for code snippets, and list best practices/gotchas concisely.",
    "detailed": (
        "Be exhaustive: provide multi-paragraph details for each subtask, including troubleshooting, alternatives, and performance notes. "
        "Provide a line-by-line explanation for code snippets. Be thorough with best practices and gotchas."
    ),
}

SCHEMA_EXAMPLE = Answer.model_json_schema()

def classify_context(query: str) -> str:
    """Classify query into Unity / Unreal / Shader / General based on keywords."""
    q = query.lower()
    if any(word in q for word in ["unity", "c#", "monobehaviour", "gameobject", "xr interaction toolkit"]):
        return "Unity"
    if any(word in q for word in ["unreal", "blueprint", "c++", "actor", "pawn", "metahuman"]):
        return "Unreal"
    if any(word in q for word in ["shader", "hlsl", "glsl", "material", "shading", "surface shader"]):
        return "Shader"
    return "General"

async def _search_web(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """Best-effort web search using Serper if key is available; otherwise return []."""
    if not SERPER_KEY:
        return []
    try:
        resp = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": SERPER_KEY, "Content-Type": "application/json"},
            json={"q": query, "num": num_results},
            timeout=10,
        )
        data = resp.json()
        out = []
        for item in data.get("organic", [])[:num_results]:
            out.append({
                "title": item.get("title", "No Title"),
                "url": item.get("link", "#"),
            })
        return out
    except Exception:
        return []

def generate_structured_answer(
    query: str,
    target: str = "AR/VR Developer",
    verbosity: str = "normal",
    max_output_tokens: int = 2000,
    live_mode: bool = False,
) -> Dict[str, Any]:
    return asyncio.run(_generate_structured_answer_async(query, target, verbosity, max_output_tokens, live_mode))

async def _generate_structured_answer_async(
    query: str,
    target: str = "AR/VR Developer",
    verbosity: str = "normal",
    max_output_tokens: int = 2000,
    live_mode: bool = False,
) -> Dict[str, Any]:

    q = (query or "").lower().strip()

    # Explicit context classification
    context = classify_context(query)
    target = f"{context} Developer"

    # Quick intents (always include all required fields)
    if q in ["hi", "hello", "hey"]:
        return Answer(
            context=context,
            target=target,
            difficulty="beginner",
            subtasks=[Subtask(title="Greeting", details="👋 Hi, how can I help with AR/VR today?", steps=[])]
        ).model_dump()

    if q in ["bye", "goodbye", "see you"]:
        return Answer(
            context=context,
            target=target,
            difficulty="beginner",
            subtasks=[Subtask(title="Farewell", details="👋 Goodbye, happy coding in XR!", steps=[])]
        ).model_dump()

    # Reject off-topic queries
    if not any(x in q for x in ["ar","vr","xr","unity","unreal","openxr","oculus","hololens","mixed reality","shader","meta quest","pico","steamvr"]):
        return Answer(
            context=context,
            target=target,
            difficulty="beginner",
            subtasks=[Subtask(title="Not Supported", details="❌ Sorry, I can only assist with AR/VR development topics like Unity XR, Unreal Engine, OpenXR, Mixed Reality, and shaders.", steps=[])]
        ).model_dump()

    docs: List[DocRef] = []
    doc_text = ""
    if live_mode:
        results = await _search_web(query, num_results=5)
        docs = [DocRef(title=r["title"], url=r["url"]) for r in results]
        if docs:
            doc_text = "\n\nGrounding Information from Web Search:\n" + "\n".join([f"- Title: {d.title}\n  URL: {d.url}" for d in docs])

    prompt = f"""
You are CodeXR, an expert AR/VR coding assistant. Your goal is to provide comprehensive, structured answers to developer queries related to AR/VR development.
Your responses MUST be valid JSON, strictly adhering to the following Pydantic schema:
{json.dumps(SCHEMA_EXAMPLE, indent=2)}

Ensure ALL fields from the schema are included, even if empty (e.g., [] for lists, null for optional objects).
The `context`, `target`, and `difficulty` fields should be inferred from the query and context.
Provide detailed steps, and if a code snippet is required, include language, filename, code, and explanation.
Always include best_practices and gotchas relevant to the query, even if short.
If web search results are provided, integrate information from them into your answer, especially for docs.

User Query: {query}
Verbosity Level: {_VERBOSITY.get(verbosity, _VERBOSITY['normal'])}
{doc_text}

Remember: Output ONLY the JSON. No conversational text outside the JSON.
"""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": max_output_tokens,
                "temperature": 0.2,
                "response_mime_type": "application/json"
            },
        )
        parsed = json.loads(resp.text)

        # ✅ Validate with schema — fall back gracefully if invalid
        try:
            validated = Answer.model_validate(parsed)
            return validated.model_dump()
        except Exception as ve:
            return Answer(
                context=context,
                target=target,
                difficulty="beginner",
                subtasks=[Subtask(title="Validation Error", details=f"Response validation failed: {ve}", steps=[])]
            ).model_dump()

    except json.JSONDecodeError as je:
        return Answer(
            context=context,
            target=target,
            difficulty="beginner",
            subtasks=[Subtask(title="JSON Parse Error", details=f"Failed to parse LLM response as JSON: {je}", steps=[])]
        ).model_dump()

    except Exception as e:
        return Answer(
            context=context,
            target=target,
            difficulty="beginner",
            subtasks=[Subtask(title="Gemini Error", details=f"Error calling Gemini API: {e}", steps=[])]
        ).model_dump()
