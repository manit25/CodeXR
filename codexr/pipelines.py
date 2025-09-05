import os, requests, time
import google.generativeai as genai

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
SERPER_KEY = os.getenv("SERPER_API_KEY")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def run_pipeline(query: str, live=False, verbosity="normal"):
    q_lower = query.lower().strip()

    if q_lower in ["hi", "hello", "hey"]:
        return {"subtasks":[{"title":"Greeting","details":"Hi 👋 How can I help with AR/VR development today?"}]}
    if q_lower in ["bye", "goodbye"]:
        return {"subtasks":[{"title":"Farewell","details":"Goodbye 👋 Have a great day coding AR/VR!"}]}
    if not any(x in q_lower for x in ["ar","vr","xr","unity","unreal","openxr","oculus","hololens"]):
        return {"subtasks":[{"title":"Not Supported","details":"❌ Sorry, I can only assist with AR/VR development."}]}

    docs = []
    if live and SERPER_KEY:
        try:
            resp = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": SERPER_KEY, "Content-Type": "application/json"},
                json={"q": query, "num": 5}
            )
            data = resp.json()
            for item in data.get("organic", []):
                docs.append({"title": item.get("title"), "url": item.get("link")})
        except Exception as e:
            docs.append({"title":"Search failed","url":str(e)})

    text = "⚠️ Gemini API not configured."
    if GEMINI_KEY:
        try:
            # Use new stable model
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"You are CodeXR, an expert AR/VR coding assistant. Give a {verbosity} response.\nQuery: {query}"
            resp = model.generate_content(prompt)
            text = resp.text.strip()
        except Exception as e:
            text = f"[Gemini error: {e}]"

    return {
        "target":"AR/VR Developers",
        "difficulty":"Intermediate",
        "subtasks":[{"title":"Response","details":text}],
        "snippet":{"filename":"example.cs","language":"csharp","code":"// Example code","explanation":"Sample placeholder."},
        "docs":docs,
        "timestamp":int(time.time())
    }
