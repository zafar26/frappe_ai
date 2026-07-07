"""
Converts Qwen2.5-0.5B-Instruct (or any Hugging Face causal LM) into a
quantized GGUF file for fast CPU inference via llama.cpp / llama-cpp-python.

This is a standalone, one-time setup script -- it is NOT part of the
Frappe app itself and doesn't run inside `bench`. Run it once on your
machine (or the bench server) to produce a .gguf file, then point
Frappe AI Settings at that file.

Requirements (install before running):
    pip install transformers torch huggingface_hub --break-system-packages
    sudo apt install build-essential cmake git -y

Usage:
    python scripts/convert_to_gguf.py
    python scripts/convert_to_gguf.py --model Qwen/Qwen2.5-0.5B-Instruct --quant q4_k_m
    python scripts/convert_to_gguf.py --output-dir /path/to/store/gguf
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

LLAMA_CPP_REPO = "https://github.com/ggerganov/llama.cpp.git"

QUANT_INFO = {
    "f16":    {"size": "~1GB",   "ram": "2GB+",   "quality": "Best"},
    "q8_0":   {"size": "~530MB", "ram": "1GB+",   "quality": "Very Good"},
    "q4_k_m": {"size": "~320MB", "ram": "512MB+", "quality": "Good (recommended)"},
    "q2_k":   {"size": "~200MB", "ram": "256MB+", "quality": "Acceptable"},
}


def run(cmd, cwd=None):
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def ensure_llama_cpp(work_dir: Path) -> Path:
    """Clone and build llama.cpp if not already present."""
    llama_cpp_dir = work_dir / "llama.cpp"

    if not llama_cpp_dir.exists():
        print("Cloning llama.cpp...")
        run(["git", "clone", "--depth", "1", LLAMA_CPP_REPO, str(llama_cpp_dir)])
    else:
        print("llama.cpp already cloned, skipping.")

    print("Installing llama.cpp's Python conversion requirements...")
    run([
        sys.executable, "-m", "pip", "install", "--break-system-packages",
        "-r", str(llama_cpp_dir / "requirements.txt"),
    ])

    build_dir = llama_cpp_dir / "build"
    quantize_bin = build_dir / "bin" / "llama-quantize"
    if not quantize_bin.exists():
        print("Building llama.cpp (this compiles the quantize tool, a few minutes)...")
        run(["cmake", "-B", "build"], cwd=llama_cpp_dir)
        run(["cmake", "--build", "build", "--config", "Release", "-j"], cwd=llama_cpp_dir)
    else:
        print("llama.cpp already built, skipping.")

    return llama_cpp_dir


def convert_and_quantize(model_name: str, quant_type: str, output_dir: Path, work_dir: Path):
    if quant_type not in QUANT_INFO:
        print(f"Unknown quant type '{quant_type}'. Choose from: {list(QUANT_INFO)}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    llama_cpp_dir = ensure_llama_cpp(work_dir)

    safe_name = model_name.replace("/", "_")
    f16_path = output_dir / f"{safe_name}_f16.gguf"
    quant_path = output_dir / f"{safe_name}_{quant_type}.gguf"

    if not f16_path.exists():
        print(f"\nConverting {model_name} to GGUF (f16 intermediate)...")
        convert_script = llama_cpp_dir / "convert_hf_to_gguf.py"
        run([
            sys.executable, str(convert_script),
            "--outfile", str(f16_path),
            "--outtype", "f16",
            model_name,
        ])
    else:
        print(f"f16 GGUF already exists at {f16_path}, skipping conversion.")

    if quant_type == "f16":
        print(f"\nDone. f16 GGUF ready at: {f16_path}")
        return f16_path

    print(f"\nQuantizing to {quant_type}...")
    quantize_bin = llama_cpp_dir / "build" / "bin" / "llama-quantize"
    run([str(quantize_bin), str(f16_path), str(quant_path), quant_type.upper()])

    print(f"\nDone. Quantized GGUF ready at: {quant_path}")
    return quant_path


def main():
    parser = argparse.ArgumentParser(description="Convert a Hugging Face model to quantized GGUF.")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct",
                         help="Hugging Face model repo (default: Qwen/Qwen2.5-0.5B-Instruct)")
    parser.add_argument("--quant", default="q4_k_m", choices=list(QUANT_INFO),
                         help="Quantization type (default: q4_k_m -- good balance of size/quality)")
    parser.add_argument("--output-dir", default="./gguf_models",
                         help="Where to save the .gguf file (default: ./gguf_models)")
    parser.add_argument("--work-dir", default="./.gguf_build",
                         help="Where to clone/build llama.cpp (default: ./.gguf_build)")
    args = parser.parse_args()

    print("Quantization options:")
    for name, info in QUANT_INFO.items():
        marker = " <-- selected" if name == args.quant else ""
        print(f"  {name:8s} size={info['size']:8s} ram={info['ram']:8s} quality={info['quality']}{marker}")
    print()

    output_dir = Path(args.output_dir).resolve()
    work_dir = Path(args.work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    gguf_path = convert_and_quantize(args.model, args.quant, output_dir, work_dir)

    print("\n" + "=" * 60)
    print("Next step: point Frappe AI Settings at this file.")
    print(f"  GGUF Model Path: {gguf_path}")
    print("Set 'Model Backend' to 'GGUF (llama.cpp)' in Frappe AI Settings,")
    print("paste the path above into 'GGUF Model Path', then warm up again:")
    print("  bench --site <your-site> execute frappe_ai.setup.warm_up_models.run")
    print("=" * 60)


if __name__ == "__main__":
    main()
