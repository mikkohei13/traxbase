import os
from datetime import datetime

from dotenv import load_dotenv
from google import genai
from google.genai import types

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


if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    generate_image(
        prompt="cute dragon 1980s retro kawaii style, on a black background.",
        output_file=f"./traxbase/images/{timestamp}_1980s_arcade_retro_game_monster_image.png",
    )
