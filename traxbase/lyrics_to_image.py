import os
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

from llm_json_parser import parse_image_prompt_json, FALLBACK_DEFAULTS

load_dotenv()

client = genai.Client(
    vertexai=True,
    project=os.environ["GOOGLE_CLOUD_PROJECT"],
    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
)


def generate_image(prompt: str, output_file: str = "output.png"):
    response = client.models.generate_images(
        model="imagen-3.0-fast-generate-001",
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="1:1",
        ),
    )
    response.generated_images[0].image.save(output_file)
    print(f"Image saved to {output_file}")


def lyrics_to_prompt(title: str, style: str, lyrics: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Title: {title}\nStyle: {style}\nLyrics: {lyrics}",
        config={
            "system_instruction": (
                "Based on the following song details, decide a variation concept, artistic style, and a color palette suitable to illustrate the song and capture it's mood.\nOutput these in the following json format, with maximum of 256 characters for each field. Don't include anything else in the output. { \"variation_concept\": \"...\", \"artistic_style\": \"...\", \"color_palette\": \"...\" }"
            ),
        },
    )
    raw_text = response.text if response.text else None
    return raw_text


if __name__ == "__main__":
    title = "Second Place"
    style = "soft rock, acoustic ballad, chillwave, gentle young male vocals, youthful indie, hopeful, singer-songwriter, mellow tempo..."
    lyrics = """
[Intro]
The lights were never meant for me
Still I stood where I could see
The echo of a distant race
A quiet heart, a slower pace

[Verse 1]
I trained to be the one in gold
Chased every line I’d ever told
But somewhere on the way to more
I found a love worth losing for
You weren’t the prize, you were the light
The thing I missed in every fight
I let go of the need to win
And you let something new begin

[Chorus]
Second place, but first with you
Didn’t need the crowd to prove
All I wanted, all along
Was where your quiet hands belong
...
    """
    print(f"Generating image prompt from lyrics...")

    try:
        raw_response = lyrics_to_prompt(title, style, lyrics)
        prompt_fields = parse_image_prompt_json(raw_response)
    except Exception as e:
        print(f"Error generating prompt, using fallback defaults: {e}")
        prompt_fields = dict(FALLBACK_DEFAULTS)

    image_prompt = (
        f"{title}, {prompt_fields['variation_concept']}"
        f" in the style of {prompt_fields['artistic_style']}"
        f" and color palette of {prompt_fields['color_palette']}"
    )

    print(f"Prompt fields: {prompt_fields}")

    print(f"Image prompt: {image_prompt}")

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    generate_image(prompt=image_prompt, output_file=f"./traxbase/images/{timestamp}_{title}.png")
