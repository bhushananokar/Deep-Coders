import os
import requests
import json
import base64
import io
import time
from PIL import Image
import streamlit as st

class DalleVisualizer:
    def __init__(self, api_key=None):
        self.api_key = ""
        self.api_url = "https://api.openai.com/v1/images/generations"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def generate_image(self, prompt, size="1024x1024", model="dall-e-3", quality="standard", style="vivid"):
        """
        Generate an image using DALL-E based on a prompt.
        
        Args:
            prompt: The text prompt to generate an image from
            size: Image size (1024x1024, 1024x1792, or 1792x1024)
            model: DALL-E model to use (dall-e-2 or dall-e-3)
            quality: Image quality (standard or hd) - only for dall-e-3
            style: Image style (vivid or natural) - only for dall-e-3
            
        Returns:
            PIL Image object or None on failure
        """
        if not self.api_key:
            st.error("DALL-E API key not provided. Unable to generate visualization.")
            return None
            
        payload = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": size
        }
        
        # Add DALL-E 3 specific parameters
        if model == "dall-e-3":
            payload["quality"] = quality
            payload["style"] = style
            
        try:
            with st.spinner("Generating visualization with DALL-E..."):
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code != 200:
                    st.error(f"DALL-E API error: {response.status_code} - {response.text}")
                    return None
                    
                data = response.json()
                
                if not data or "data" not in data or not data["data"]:
                    st.error("No image data received from DALL-E API")
                    return None
                    
                # Get the image URL from the API response
                image_url = data["data"][0]["url"]
                
                # Download the image
                img_response = requests.get(image_url, timeout=30)
                if img_response.status_code != 200:
                    st.error(f"Failed to download image: {img_response.status_code}")
                    return None
                    
                # Convert to PIL Image
                image = Image.open(io.BytesIO(img_response.content))
                return image
                
        except requests.exceptions.Timeout:
            st.error("DALL-E API request timed out")
            return None
        except requests.exceptions.RequestException as e:
            st.error(f"DALL-E API request failed: {e}")
            return None
        except Exception as e:
            st.error(f"Error generating image: {e}")
            return None
            
    def visualize_concept(self, concept_text, context=None):
        """
        Create a visualization of an educational concept.
        
        Args:
            concept_text: The text describing the concept to visualize
            context: Additional context to help with visualization
            
        Returns:
            PIL Image object or None on failure
        """
        # Create a prompt focused on educational visualization
        prompt_base = "Create a clear, detailed educational diagram or illustration of"
        
        if context:
            prompt = f"{prompt_base} {concept_text}. Context: {context}. Make it visually engaging and educational, suitable for students. Include relevant labels and visual elements to aid understanding."
        else:
            prompt = f"{prompt_base} {concept_text}. Make it visually engaging and educational, suitable for students. Include relevant labels and visual elements to aid understanding."
            
        # Limit prompt length
        if len(prompt) > 1000:
            prompt = prompt[:997] + "..."
            
        return self.generate_image(prompt)
        
    def visualize_mathematics(self, math_concept):
        """Specialized method for visualizing mathematical concepts."""
        prompt = f"Create a clear mathematical visualization or diagram explaining {math_concept}. Include relevant formulas, graphs, and visual elements to make it educational and easy to understand. Use a clean, organized layout with clear labels."
        return self.generate_image(prompt)
        
    def visualize_instructions(self, instructions):
        """Specialized method for visualizing step-by-step instructions."""
        prompt = f"Create a clear step-by-step visual guide showing how to: {instructions}. Include numbered steps, clear illustrations for each step, and arrange them in a logical flow. Make it educational and easy to follow."
        return self.generate_image(prompt)
        
    def save_image(self, image, filename=None):
        """Save the generated image to a file."""
        if image is None:
            return None
            
        if filename is None:
            timestamp = int(time.time())
            filename = f"dalle_visualization_{timestamp}.png"
            
        try:
            image.save(filename)
            return filename
        except Exception as e:
            st.error(f"Error saving image: {e}")
            return None
