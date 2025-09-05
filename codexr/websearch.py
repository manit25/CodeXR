import os, httpx
from typing import List, Dict, Any

SERPER_API_KEY = os.getenv("SERPER_API_KEY")

async def search_web(query: str, num_results: int = 3) -> List[Dict[str, Any]]:
    if not SERPER_API_KEY:
        return []
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": num_results}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.post(url, headers=headers, json=payload)
            results = r.json()
        except Exception:
            return []
    docs = []
    for item in results.get("organic", []):
        docs.append({"title": item.get("title"), "url": item.get("link")})
    return docs
