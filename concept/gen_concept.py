"""Generate BRUMBLE concept art with Nano Banana (Gemini image gen).

Key: set GEMINI_API_KEY in the environment, or point GEMINI_ENV_FILE at a
.env file containing a GEMINI_API_KEY=... line.
Refs: the brand avatar plus a real gameplay screenshot (drop one next to this
script as gameplay_ref.png, optional).

Usage: python gen_concept.py [--wide] [scene names...]
  --wide renders 16:9 instead of 9:16 and adds a -wide suffix.
  Scene names filter which scenes render (default: all).
"""
import mimetypes
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
REFS = [p for p in (
    HERE.parent / "assets" / "brumble-avatar-1024.png",
    HERE / "gameplay_ref.png",
) if p.exists()]

STYLE = """
STYLE: Voxel / blocky 3D render, Minecraft-adjacent but rounder and friendlier,
thick dark outlines on the bees matching the logo mascot (ink color #221A10,
honey gradient #FFD84D to #F0A500, cream highlights #FFF6DA). Soft volumetric
golden-hour lighting, gentle depth of field, saturated storybook palette.
Tone: adorable on the surface, mischievously competitive underneath.

COMPOSITION: vertical 9:16, key subjects centered with generous margins,
nothing important within the outer 15% of the frame, clean negative space in
the top third for a title overlay. No text, no watermark, no logo, no humans.
"""

HEADER = """Key art for "BRUMBLE", a cozy-but-competitive voxel bee strategy game.
Match the mascot style and color identity of the first attached image (the logo
mascot), and the blocky voxel world of the second attached image (a real
gameplay screenshot).
"""

VIEW = """
CAMERA: Top-down real-time-strategy view, camera high above the battlefield
tilted about 60 degrees, like the attached gameplay screenshot but more epic
and polished. The whole meadow reads like an RTS map: units small but crisp,
long warm shadows, clear silhouettes from above.
"""

SCENES = {
    "keyart": """SCENE: An RTS map view of the full meadow battlefield at
golden hour. Two rival voxel beehives at opposite corners like bases, each on
its own grass clearing under a blocky tree. Between them: patches of fat voxel
sunflowers as resource nodes. The QUEEN BEE, twice worker size with a tiny
golden crown, leads a V-formation swarm of eight worker bees across the middle
of the map, dotted flight-trail lines curving behind them. A few workers sit
on sunflower heads harvesting, tiny nectar drops glowing.""",
    "heist": """SCENE: An RTS map view of a chase in progress: a lone worker
bee carrying a glowing amber nectar drop races along a curving dotted flight
path toward its hive at the bottom of the map, while three rival bees cut
across the field on an intercept course, their own dotted trails converging on
it. Sunflower patches and long evening shadows below.""",
    "laststand": """SCENE: An RTS map view at dusk of a hive under siege: the
defending hive in the center clearing with a ring of worker bees hovering in
formation around it, the large crowned queen at the entrance, while a wide arc
of attacker bees closes in from the map edges, their dotted approach trails
fanning inward. Warm hive glow against cool blue evening grass.""",
}

def main():
    key = os.environ.get("GEMINI_API_KEY", "")
    env_file = os.environ.get("GEMINI_ENV_FILE", "")
    if not key and env_file and pathlib.Path(env_file).exists():
        for line in pathlib.Path(env_file).read_text().splitlines():
            if line.startswith("GEMINI_API_KEY="):
                key = line.split("=", 1)[1].strip()
    if not key:
        sys.exit("set GEMINI_API_KEY or GEMINI_ENV_FILE")

    wide = "--wide" in sys.argv
    aspect = "16:9" if wide else "9:16"
    suffix = "-topdown-wide" if wide else "-topdown"
    wanted = [a for a in sys.argv[1:] if not a.startswith("--")]

    from google import genai
    from google.genai import types

    from PIL import Image
    import io

    client = genai.Client(
        api_key=key,
        http_options=types.HttpOptions(timeout=300_000))
    parts = []
    for r in REFS:
        img = Image.open(r).convert("RGB")
        img.thumbnail((640, 640), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=88)
        parts.append(types.Part.from_bytes(
            data=buf.getvalue(), mime_type="image/jpeg"))

    cfg = None
    try:
        cfg = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=aspect))
    except Exception:
        pass

    for name, scene in SCENES.items():
        if wanted and name not in wanted:
            continue
        print("generating", name, "...", flush=True)
        style = STYLE.replace("vertical 9:16", "widescreen 16:9") if wide else STYLE
        prompt = HEADER + scene + VIEW + style
        out = HERE / f"brumble-concept-{name}{suffix}.png"
        kwargs = {"model": "gemini-2.5-flash-image",
                  "contents": [prompt] + parts}
        if cfg:
            kwargs["config"] = cfg
        try:
            resp = client.models.generate_content(**kwargs)
        except Exception as e:
            print("  retrying without image_config:", type(e).__name__, flush=True)
            kwargs.pop("config", None)
            resp = client.models.generate_content(**kwargs)
        saved = False
        for part in resp.candidates[0].content.parts:
            inline = getattr(part, "inline_data", None)
            if inline and inline.data:
                out.write_bytes(inline.data)
                saved = True
                break
        print(name, "->", out if saved else "NO IMAGE RETURNED")

if __name__ == "__main__":
    main()
