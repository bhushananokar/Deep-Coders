import openai
import requests
import os

# Set your API Key
openai.api_key = ""

def generate_image(prompt, save_path="generated_image.png"):
    response = openai.images.generate(
        model="dall-e-3",   # or dall-e-2
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    print(f"Image generated: {image_url}")

    img_data = requests.get(image_url).content
    with open(save_path, 'wb') as handler:
        handler.write(img_data)

    print(f"Image saved to {save_path}")

if __name__ == "__main__":
    prompt = input("Enter a prompt for the image: ")
    generate_image(prompt)
