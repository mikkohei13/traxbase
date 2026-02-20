import json
import logging
import os
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

from traxbase.llm_json_parser import parse_image_prompt_json, FALLBACK_DEFAULTS

load_dotenv()

log = logging.getLogger(__name__)

client = genai.Client(
    vertexai=True,
    project=os.environ["GOOGLE_CLOUD_PROJECT"],
    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
)


def generate_image(prompt: str, output_file: str):
    response = client.models.generate_images(
        model="imagen-3.0-fast-generate-001",
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="1:1",
        ),
    )
    response.generated_images[0].image.save(output_file)
    log.info("Image saved to %s", output_file)


def remove_short_tokens(text: str) -> str:
    """Remove single/double letter words and short numbers/version tags from text.

    Examples:
        "Song Title A" -> "Song Title"
        "This is a song title" -> "This song title"
        "My Song v2" -> "My Song"
        "My song 67" -> "My song"
        "Long song name here vX" -> "Long song name here"
    """
    tokens = text.split()
    cleaned = [t for t in tokens if not re.match(r'^(v?\d{1,2}|[a-zA-Z]{1,2})$', t)]
    return ' '.join(cleaned).strip() if cleaned else text


def lyrics_to_prompt(title: str, style: str, lyrics: str, description: str = "") -> str:
    system_instruction = """
Based on the following song details, decide a variation concept, artistic style, and a color palette suitable to illustrate the song and capture it's mood. Favor unique, colorful, and creative concepts that work in small sizes. Also specify background color, which should be neither black nor dark.
Output these in the following json format, with maximum of 256 characters for each field. Don't include anything else in the output. 
{ "variation_concept": "...", "artistic_style": "...", "color_palette": "..." }
    """
    print(f"[lyrics_to_image] System instruction: {system_instruction}")
#    print(f"[lyrics_to_image] Song details: Title: {title}\nStyle: {style}\nLyrics: {lyrics}")

    # If title contains more than 4 numbers, it is probably a UUID, replace with generic title
    if re.search(r'\d{4,}', title):
        title = "Album cover art image"

    # If title has single letters or version numbers, remove them (e.g. "Song Title A" should become "Song Title", and "A Song title" should become "Song title")
    title = remove_short_tokens(title)

    # Truncate the song details
    title = title[:128]
    style = style[:256]
    description = description[:512]
    lyrics = lyrics[:1024]

    # If description contains # or //, remove everything after it
    if '#' in description:
        description = description.split('#')[0]
    if '//' in description:
        description = description.split('//')[0]

    llm_prompt = f"Title: {title}\nStyle: {style}"
    if description:
        llm_prompt += f"\nDescription: {description}"
    llm_prompt += f"\nLyrics: {lyrics}"
    print(f"[lyrics_to_image] Gemini request:\n{llm_prompt}")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=llm_prompt,
        config={"system_instruction": system_instruction},
    )
    raw_text = response.text if response.text else None
    print(f"[lyrics_to_image] Gemini response: {raw_text}")
    return raw_text


def generate_track_image(title: str, style: str, lyrics: str, base_path: str, *, description: str = ""):
    """Full pipeline: song details -> Gemini prompt -> Imagen image -> save to disk.

    Saves three files relative to base_path (path without extension):
      - {base_path}_original.png  (full-size Imagen output)
      - {base_path}.png           (200x200 thumbnail)
      - {base_path}_prompts.json  (llm_prompt and image_prompt)
    """
    try:
        raw_response = lyrics_to_prompt(title, style, lyrics, description)
        prompt_fields = parse_image_prompt_json(raw_response)
    except Exception:
        log.warning("Gemini prompt generation failed, using fallback defaults", exc_info=True)
        prompt_fields = dict(FALLBACK_DEFAULTS)

    image_prompt = (
        f"{title}, {prompt_fields['variation_concept']}"
        f" in the style of {prompt_fields['artistic_style']}"
        f" and color palette of {prompt_fields['color_palette']}"
    )
    print(f"[lyrics_to_image] Imagen prompt: {image_prompt}")

    original_path = base_path + "_original.png"
    thumb_path = base_path + ".png"
    prompts_path = base_path + "_prompts.json"

    generate_image(prompt=image_prompt, output_file=original_path)
    print(f"[lyrics_to_image] Original saved to {original_path}")

    with Image.open(original_path) as img:
        img.resize((200, 200), Image.LANCZOS).save(thumb_path)
    print(f"[lyrics_to_image] Thumbnail saved to {thumb_path}")

    llm_prompt = f"Title: {title}\nStyle: {style}"
    if description:
        llm_prompt += f"\nDescription: {description}"
    llm_prompt += f"\nLyrics: {lyrics}"
    with open(prompts_path, "w") as f:
        json.dump({"llm_prompt": llm_prompt, "image_prompt": image_prompt}, f, indent=2)
    print(f"[lyrics_to_image] Prompts saved to {prompts_path}")
