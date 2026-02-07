import base64
import os
from io import BytesIO

import litellm
import requests
import yaml
from dotenv import load_dotenv
from PIL import Image

load_dotenv()


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


def get_ai_response(model_id, history, temp=0.7, tokens=1000):
    """Text generation with simplified parameters for 2026."""
    try:
        response = litellm.completion(
            model=model_id, messages=history, temperature=temp, max_tokens=tokens
        )
        return response.choices[0].message.content, response.usage
    except Exception as e:
        raise RuntimeError(f"Text Error: {str(e)}") from e


def generate_image(model_id, prompt, n=1, size="1024x1024"):
    """Unified Image generation. Removed 'quality' to support new 2026 API standards. Finalized 2026 Multi-Provider Image Logic."""
    provider, actual = _split_model_id(model_id)

    try:
        # 1. OpenAI / Google
        if provider in ["openai", "gemini"]:
            # Standardize for Gemini (1024x1024 only) vs OpenAI
            # LiteLLM handles both OpenAI and Google Gemini 3.0 Image models
            resp = litellm.image_generation(
                model=model_id, prompt=prompt, n=n, size="1024x1024"  # Standardized for 2026
            )
            results = []
            for item in resp.data:
                b64 = getattr(item, "b64_json", None)
                results.append(_b64_to_pil(b64) if b64 else item.url)
            return results

        # 2. xAI (Grok) - Uses 1:1 Aspect Ratio logic for 2026
        if provider == "xai":
            api_key = os.getenv("XAI_API_KEY")
            # Note: Ensure credits are added at https://console.x.ai/
            r = requests.post(
                "https://api.x.ai/v1/images/generations",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": actual, "prompt": prompt, "n": n, "aspect_ratio": "1:1"},
            )
            if r.status_code != 200:
                raise RuntimeError(f"xAI Error: {r.json().get('error', 'Unknown Error')}")
            return [img.get("url") for img in r.json().get("data", [])]

        # 3. Hugging Face (New 2026 Router)
        if provider == "hf":
            token = os.getenv("HUGGINGFACE_API_KEY")
            # FIX: We use 'actual' here (stabilityai/...) to avoid the 'hf/' prefix in the URL
            router_url = f"https://router.huggingface.co/hf-inference/models/{actual}"
            r = requests.post(
                router_url, headers={"Authorization": f"Bearer {token}"}, json={"inputs": prompt}
            )
            if r.status_code != 200:
                raise RuntimeError(f"HF Error: {r.text}")
            return [Image.open(BytesIO(r.content)).convert("RGB")]

    except Exception as e:
        raise RuntimeError(f"Image API Error: {str(e)}") from e
