import base64
import json
import os
from io import BytesIO

import requests
import yaml
from dotenv import load_dotenv
from PIL import Image

load_dotenv()


# --- PERSISTENCE HELPERS ---
def save_threads(threads):
    """Saves the thread dictionary to a local JSON file."""
    path = os.path.join("projects", "ai_hub", "chat_history.json")
    with open(path, "w") as f:
        json.dump(threads, f, indent=4)


def load_threads():
    """Loads threads from JSON or returns an empty dict if not found."""
    path = os.path.join("projects", "ai_hub", "chat_history.json")
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


# --- PROVIDER HELPERS ---
def _split_model_id(model_id: str) -> tuple[str, str]:
    if "/" not in model_id:
        return "unknown", model_id
    provider, actual = model_id.split("/", 1)
    return provider.strip(), actual.strip()


def _b64_to_pil(b64_data: str) -> Image.Image:
    raw = base64.b64decode(b64_data)
    return Image.open(BytesIO(raw)).convert("RGB")


def load_model_garden():
    path = os.path.join("projects", "ai_hub", "config", "models.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


# --- THE SPEED FIX: STREAMING ---
def get_ai_response_stream(model_id, history, temp=0.7, tokens=1000):
    """Returns a stream generator. 'import litellm' is inside to speed up app boot."""
    import litellm  # Deferred import

    try:
        response = litellm.completion(
            model=model_id, messages=history, temperature=temp, max_tokens=tokens, stream=True
        )
        return response
    except Exception as e:
        raise RuntimeError(f"Streaming Error: {str(e)}") from e


# --- IMAGE GENERATION ---
def generate_image(model_id, prompt, n=1, size="1024x1024"):
    import litellm  # Deferred import

    provider, actual = _split_model_id(model_id)
    try:
        if provider in ["openai", "gemini"]:
            final_size = "1024x1024" if provider == "gemini" else size
            resp = litellm.image_generation(model=model_id, prompt=prompt, n=n, size=final_size)
            results = []
            for item in resp.data:
                b64 = getattr(item, "b64_json", None)
                results.append(_b64_to_pil(b64) if b64 else item.url)
            return results

        if provider == "xai":
            api_key = os.getenv("XAI_API_KEY")
            r = requests.post(
                "https://api.x.ai/v1/images/generations",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": actual, "prompt": prompt, "n": n, "aspect_ratio": "1:1"},
            )
            r.raise_for_status()
            return [img.get("url") for img in r.json().get("data", [])]

        if provider == "hf":
            token = os.getenv("HUGGINGFACE_API_KEY")
            router_url = f"https://router.huggingface.co/hf-inference/models/{actual}"
            r = requests.post(
                router_url, headers={"Authorization": f"Bearer {token}"}, json={"inputs": prompt}
            )
            r.raise_for_status()
            return [Image.open(BytesIO(r.content)).convert("RGB")]

    except Exception as e:
        raise RuntimeError(f"Image API Error: {str(e)}") from e
