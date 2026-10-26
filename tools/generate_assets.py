
import json
import shutil
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "src/main/resources"
PACK = RESOURCES / "resourcepacks/emoji_font"
ASSETS = PACK / "assets/minecraft"

TEXTURES = ASSETS / "textures/font/emoji"
FONT_DIR = ASSETS / "textures/font"
FONT_JSON = ASSETS / "font/default.json"

EMOJI_ZIP = ROOT / "emoji.zip"
FONT_ZIP = ROOT / "font.zip"
DATA_JSON = ROOT / "emoji_data.json"

for path in (TEXTURES, FONT_DIR, FONT_JSON.parent):
    path.mkdir(parents=True, exist_ok=True)

for required in (EMOJI_ZIP, FONT_ZIP, DATA_JSON):
    if not required.exists():
        raise SystemExit(f"Missing required file: {required.name}")

# Create the resource-pack metadata.
(PACK / "pack.mcmeta").write_text(
    json.dumps(
        {
            "pack": {
                "pack_format": 15,
                "description": "Emoji Font for Minecraft 1.20.1"
            }
        },
        indent=2
    ),
    encoding="utf-8"
)

# Extract emoji images directly into the resource pack.
with zipfile.ZipFile(EMOJI_ZIP) as archive:
    for name in archive.namelist():
        normalized = name.replace("\\", "/")
        if not normalized.lower().endswith(".png"):
            continue

        parts = normalized.split("/")
        filename = parts[-1]

        # Ignore folders and unsafe paths; only copy PNG files.
        if not filename:
            continue

        source_data = archive.read(name)
        destination = TEXTURES / filename
        destination.write_bytes(source_data)

# Extract a font file from font.zip.
with zipfile.ZipFile(FONT_ZIP) as archive:
    candidates = [
        name for name in archive.namelist()
        if name.lower().endswith((".otf", ".ttf"))
    ]

    if not candidates:
        raise SystemExit("No .otf or .ttf file found in font.zip")

    preferred = [
        name for name in candidates
        if "inter-frozen-medium.otf" in name.lower()
    ]

    selected = preferred[0] if preferred else candidates[0]
    font_path = ROOT / "tools" / "inter-font.otf"
    font_path.parent.mkdir(parents=True, exist_ok=True)
    font_path.write_bytes(archive.read(selected))

# Build a simple bitmap atlas for basic Latin characters.
font = ImageFont.truetype(str(font_path), 13)

characters = [chr(code) for code in range(32, 256)]
columns = 16
cell_width = 16
cell_height = 16
rows = (len(characters) + columns - 1) // columns

atlas = Image.new(
    "RGBA",
    (columns * cell_width, rows * cell_height),
    (0, 0, 0, 0)
)
draw = ImageDraw.Draw(atlas)

for index, character in enumerate(characters):
    x = (index % columns) * cell_width
    y = (index // columns) * cell_height

    draw.text(
        (x + 1, y - 1),
        character,
        font=font,
        fill=(255, 255, 255, 255)
    )

atlas.save(FONT_DIR / "inter_latin.png")

character_rows = [
    "".join(characters[i:i + columns])
    for i in range(0, len(characters), columns)
]

providers = [
    {
        "type": "bitmap",
        "file": "minecraft:font/inter_latin.png",
        "ascent": 12,
        "height": 16,
        "chars": character_rows
    }
]

# Add emoji images whose symbols contain one Unicode code point.
emoji_data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
added = set()

for item in emoji_data:
    if not isinstance(item, list) or not item:
        continue

    symbol = item[0]
    if not isinstance(symbol, str) or len(symbol) != 1:
        continue

    codepoint = ord(symbol)
    filename = f"{codepoint:x}.png"

    if filename in added:
        continue

    if not (TEXTURES / filename).exists():
        continue

    providers.append(
        {
            "type": "bitmap",
            "file": f"minecraft:font/emoji/{filename}",
            "ascent": 8,
            "height": 9,
            "chars": [symbol]
        }
    )
    added.add(filename)

# Fall back to Minecraft's uniform font for missing glyphs.
providers.append(
    {
        "type": "reference",
        "id": "minecraft:uniform"
    }
)

FONT_JSON.write_text(
    json.dumps(
        {"providers": providers},
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print(f"Generated font resources. Emoji glyphs added: {len(added)}")
