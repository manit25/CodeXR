from .schema import Answer, Subtask, Snippet, DocRef

UNITY_DEMO = Answer(
    target="unity",
    difficulty="medium",
    subtasks=[
        Subtask(title="Install XR packages", steps=[
            "Open Package Manager and install 'XR Interaction Toolkit'.",
            "Enable XR Plug-in Management and select your target (OpenXR).",
        ]),
        Subtask(title="Add Teleportation Rig", steps=[
            "Add XR Origin (Action-based) to the scene.",
            "Add Teleportation Anchor/Area and Teleportation Provider.",
            "Bind input (thumbstick/touchpad) to Teleport action.",
        ]),
        Subtask(title="Configure Layers + Colliders", steps=[
            "Ensure teleportation surfaces use valid layer masks.",
            "Add colliders to ground/anchors.",
        ]),
    ],
    snippet=Snippet(
        language="csharp",
        filename="TeleportSetup.cs",
        code="using UnityEngine;\nusing UnityEngine.XR.Interaction.Toolkit;\n\npublic class TeleportSetup : MonoBehaviour\n{\n    public TeleportationProvider provider;\n    public XRRayInteractor ray;\n    void Start()\n    {\n        if (provider == null) provider = FindObjectOfType<TeleportationProvider>();\n        if (ray != null) ray.enableUIInteraction = false;\n    }\n}\n"
    ),
    gotchas=[
        "NullReferenceException if TeleportationProvider isn't assigned.",
        "Ensure XR Interaction Toolkit input actions are enabled.",
    ],
    best_practices=[
        "Keep locomotion options accessible (teleport + snap turn).",
        "Test comfort settings across devices.",
    ],
    docs=[
        DocLink(title="Unity XR Interaction Toolkit", url="https://docs.unity3d.com/Packages/com.unity.xr.interaction.toolkit@latest"),
        DocLink(title="OpenXR Plugin (Unity)", url="https://docs.unity3d.com/Packages/com.unity.xr.openxr@latest"),
    ],
    meta={"demo": True},
)

UNREAL_DEMO = Answer(
    target="unreal",
    difficulty="hard",
    subtasks=[
        Subtask(title="Enable Plugins & Modules", steps=[
            "Enable Online Subsystem (EOS/Steam) and replication in project settings.",
            "Create a GameMode that supports multiplayer.",
        ]),
        Subtask(title="Set up Player Spawning", steps=[
            "Use GameMode::ChoosePlayerStart and proper PlayerState/Controller classes.",
            "Configure NetCullDistanceSquared for replicated actors.",
        ]),
        Subtask(title="Session + Travel", steps=[
            "Create a listen server and use seamless travel.",
            "Expose Create/Find/Join Session via Blueprints or C++ wrappers.",
        ]),
    ],
    snippet=Snippet(
        language="cpp",
        filename="VRMultiplayerGameMode.cpp",
        code="#include \"VRMultiplayerGameMode.h\"\n#include \"GameFramework/PlayerStart.h\"\n\nAActor* AVRMultiplayerGameMode::ChoosePlayerStart_Implementation(AController* Player)\n{\n    return Super::ChoosePlayerStart_Implementation(Player);\n}\n"
    ),
    gotchas=[
        "Mismatched engine versions break EOS/Steam subsystems.",
        "Map travel must be server-authoritative; clients cannot open maps directly.",
    ],
    best_practices=[
        "Test with -log and net pktlag/pktloss to simulate conditions.",
        "Use RPCs sparingly; prefer replicated properties.",
    ],
    docs=[
        DocLink(title="UE5 Networking Overview", url="https://docs.unrealengine.com/5.0/en-US/overview-of-networking-in-unreal-engine/"),
        DocLink(title="Online Subsystem (UE)", url="https://docs.unrealengine.com/4.27/en-US/InteractiveExperiences/Online/Subsystems/"),
    ],
    meta={"demo": True},
)

SHADER_DEMO = Answer(
    target="shader",
    difficulty="medium",
    subtasks=[
        Subtask(title="Choose Occlusion Strategy", steps=[
            "Use depth-based occlusion if device provides environment depth.",
            "Fallback: stencil/alpha masks via segmentation or anchors.",
        ]),
        Subtask(title="Implement Depth Test", steps=[
            "Sample environment depth texture.",
            "Discard fragments behind real-world surfaces.",
        ]),
    ],
    snippet=Snippet(
        language="hlsl",
        filename="AROcclusion.hlsl",
        code="float sceneDepth = SampleDepthTexture(i.uv);\nif (i.viewDepth > sceneDepth) { clip(-1); }\n"
    ),
    gotchas=[
        "Depth units & ranges differ per platform; normalize correctly.",
        "Beware of temporal noise in depth; add smoothing.",
    ],
    best_practices=[
        "Profile on-device; desktop preview may differ significantly.",
        "Expose tunables for smoothing and bias.",
    ],
    docs=[
        DocLink(title="ARCore Depth", url="https://developers.google.com/ar/depth/overview"),
        DocLink(title="ARKit Scene Depth", url="https://developer.apple.com/documentation/arkit/scene_depth"),
    ],
    meta={"demo": True},
)

DEMOS = {
    "unity": UNITY_DEMO,
    "unreal": UNREAL_DEMO,
    "shader": SHADER_DEMO,
}
