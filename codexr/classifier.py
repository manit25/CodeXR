from typing import Literal

def classify(query: str) -> Literal["unity", "unreal", "shader", "general"]:
    q = (query or "").lower()
    unity_terms = ["unity", "xr interaction", "teleport", "c#","openxr"]
    unreal_terms = ["unreal", "ue5", "blueprint", "c++", "multiplayer"]
    shader_terms = ["shader", "hlsl", "glsl", "shaderlab", "occlusion", "depth"]
    if any(t in q for t in unity_terms):
        return "unity"
    if any(t in q for t in unreal_terms):
        return "unreal"
    if any(t in q for t in shader_terms):
        return "shader"
    return "general"
