"""
download.py — Descarga el modelo Qwen2.5-1.5B-Instruct desde HuggingFace

Modelo elegido: Qwen/Qwen2.5-1.5B-Instruct
  - Peso: ~3GB en disco
  - Bueno para instruction following y razonamiento con herramientas
  - Soporta chat template con tool calling

  
    python agent/llm/download.py
"""

import os
from pathlib import Path

MODEL_ID   = "Qwen/Qwen2.5-1.5B-Instruct"
MODELS_DIR = Path(__file__).parent / "models"


def download_model(model_id: str = MODEL_ID, models_dir: Path = MODELS_DIR) -> Path:
    """
    Descarga el modelo desde HuggingFace Hub al directorio local.
    Si ya está descargado, no vuelve a descargarlo.
    Devuelve el path local donde está el modelo.
    """
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        raise ImportError(
            "Instala huggingface_hub primero:\n"
            "  pip install huggingface_hub transformers torch"
        )

    model_name   = model_id.split("/")[-1]
    local_path   = models_dir / model_name

    if local_path.exists() and any(local_path.iterdir()):
        print(f"Modelo ya descargado en: {local_path}")
        return local_path

    print(f"Descargando {model_id} en {local_path} ...")
    models_dir.mkdir(parents=True, exist_ok=True)

    snapshot_download(
        repo_id        = model_id,
        local_dir      = str(local_path),
        ignore_patterns= ["*.pt", "*.bin"],   # solo safetensors → más rápido
    )

    print(f"Modelo descargado correctamente en: {local_path}")
    return local_path


if __name__ == "__main__":
    path = download_model()
    print(f"\nListo. Para usar el modelo en inference.py:\n  MODEL_PATH = '{path}'")