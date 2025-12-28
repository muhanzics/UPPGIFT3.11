"""
Model manager for interacting with Ollama API.
"""

import requests
import json
from typing import List, Optional, Dict, Any
from .models import ModelConfig


class ModelManager:
    """Manages Ollama models - listing, testing, configuration."""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        """
        Initialize ModelManager.

        Args:
            ollama_url: Base URL for Ollama API
        """
        self.ollama_url = ollama_url
        self.api_endpoint = f"{ollama_url}/api/generate"
        self.tags_endpoint = f"{ollama_url}/api/tags"
        self.pull_endpoint = f"{ollama_url}/api/pull"

    def test_connection(self) -> bool:
        """
        Test connection to Ollama server.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = requests.get(self.tags_endpoint, timeout=5)
            response.raise_for_status()
            print(f"Connected to Ollama at {self.ollama_url}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Cannot connect to Ollama at {self.ollama_url}: {e}")
            return False

    def list_models(self) -> List[str]:
        """
        List all available Ollama models.

        Returns:
            List of model names
        """
        try:
            response = requests.get(self.tags_endpoint, timeout=5)
            response.raise_for_status()

            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]

            return model_names
        except requests.exceptions.RequestException as e:
            print(f"Error listing models: {e}")
            return []

    def model_exists(self, model_name: str) -> bool:
        """
        Check if a specific model is available.

        Args:
            model_name: Name of the model to check

        Returns:
            True if model exists, False otherwise
        """
        models = self.list_models()
        return model_name in models

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a model.

        Args:
            model_name: Name of the model

        Returns:
            Model information dictionary or None if not found
        """
        try:
            response = requests.get(self.tags_endpoint, timeout=5)
            response.raise_for_status()

            models = response.json().get('models', [])

            for model in models:
                if model.get('name') == model_name:
                    return model

            return None
        except requests.exceptions.RequestException as e:
            print(f"Error getting model info: {e}")
            return None

    def pull_model_generator(self, model_name: str):
        """
        Generator that yields progress updates from Ollama.
        """
        print(f"Starting pull generator for: {model_name}")
        try:
            # Now self.pull_endpoint is defined!
            response = requests.post(
                self.pull_endpoint,
                json={"name": model_name},
                stream=True,
                timeout=None
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    yield line + b'\n'

        except requests.exceptions.RequestException as e:
            print(f"Error pulling model {model_name}: {e}")
            # json is now imported, so this won't crash
            yield json.dumps({"error": str(e)}).encode('utf-8')

    def generate_response(
        self,
        prompt: str,
        model_config: ModelConfig
    ) -> Optional[str]:
        """
        Generate a response from the model.

        Args:
            prompt: The prompt to send to the model
            model_config: Model configuration

        Returns:
            Model response text or None if error
        """
        try:
            payload = {
                "model": model_config.name,
                "prompt": prompt,
                "stream": False
            }

            # Add optional parameters if specified
            options = model_config.to_ollama_options()
            if options:
                payload["options"] = options

            response = requests.post(
                self.api_endpoint,
                json=payload,
                timeout=180
            )
            response.raise_for_status()

            result = response.json()
            return result.get('response', '')

        except requests.exceptions.RequestException as e:
            print(f"Error generating response: {e}")
            return None
