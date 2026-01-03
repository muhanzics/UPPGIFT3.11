# Muhaned Mahdi
# Enes Özbek

"""
Model manager for interacting with Ollama API.
"""

import requests
import json
from typing import List, Optional, Dict, Any
from .models import ModelConfig


class ModelManager:
    """manages ollama models - listing, testing, configuration."""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        """
        initialize modelmanager.

        args:
            ollama_url: base url for ollama api
        """
        self.ollama_url = ollama_url
        self.api_endpoint = f"{ollama_url}/api/generate"
        self.tags_endpoint = f"{ollama_url}/api/tags"
        self.pull_endpoint = f"{ollama_url}/api/pull"

    def test_connection(self) -> bool:
        """
        test connection to ollama server.

        returns:
            true if connection successful, false otherwise
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
        list all available ollama models.

        returns:
            list of model names
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
        check if a specific model is available.

        args:
            model_name: name of the model to check

        returns:
            true if model exists, false otherwise
        """
        models = self.list_models()
        return model_name in models

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        get detailed information about a model.

        args:
            model_name: name of the model

        returns:
            model information dictionary or none if not found
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
        generator that yields progress updates from ollama.
        """
        print(f"Starting pull generator for: {model_name}")
        try:
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
            yield json.dumps({"error": str(e)}).encode('utf-8')

    # sends a prompt to the AI model via ollama api and returns its response
    def generate_response(
        self,
        prompt: str,
        model_config: ModelConfig
    ) -> Optional[str]:
        """
        generate a response from the model.

        args:
            prompt: the prompt to send to the model
            model_config: model configuration

        returns:
            model response text or None if error
        """
        try:
            # prepare the request payload for ollama api
            payload = {
                "model": model_config.name,
                "prompt": prompt,
                "stream": False
            }

            # add AI parameters like temperature to control model behavior
            options = model_config.to_ollama_options()
            if options:
                payload["options"] = options

            # make the http request to ollama with a timeout for long model responses
            response = requests.post(
                self.api_endpoint,
                json=payload,
                timeout=180
            )
            response.raise_for_status()

            # extract the text response from the api result
            result = response.json()
            return result.get('response', '')

        except requests.exceptions.RequestException as e:
            print(f"Error generating response: {e}")
            return None
