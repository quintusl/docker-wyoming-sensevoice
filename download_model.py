from huggingface_hub import hf_hub_download
import os
import argparse

def download_model(repo_id, destination):
    os.makedirs(destination, exist_ok=True)
    
    files = ["model.int8.onnx", "tokens.txt"]
    
    for file in files:
        print(f"Downloading {file} from {repo_id}...")
        hf_hub_download(
            repo_id=repo_id,
            filename=file,
            local_dir=destination,
            local_dir_use_symlinks=False
        )
    print("Download complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="csukuangfj/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2025-09-09")
    parser.add_argument("--out", default="/app/model")
    args = parser.parse_args()
    
    download_model(args.repo, args.out)
