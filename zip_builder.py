import os
import urllib.request
import zipfile
import shutil

# ============================
# RapidOCR 模型下载链接
# ============================
MODEL_URLS = {
    "det.onnx": "https://huggingface.co/rapidai/RapidOCR/resolve/main/models/det.onnx",
    "rec.onnx": "https://huggingface.co/rapidai/RapidOCR/resolve/main/models/rec.onnx",
    "cls.onnx": "https://huggingface.co/rapidai/RapidOCR/resolve/main/models/cls.onnx"
}

MODEL_DIR = "models"
ZIP_NAME = "math-ocr-full.zip"

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def download_models():
    ensure_dir(MODEL_DIR)
    for filename, url in MODEL_URLS.items():
        save_path = os.path.join(MODEL_DIR, filename)
        if os.path.exists(save_path):
            print(f"✔ {filename} 已存在，跳过下载")
            continue
        print(f"⬇ 正在下载 {filename} ...")
        urllib.request.urlretrieve(url, save_path)
        print(f"   → 下载完成：{save_path}")

def zip_project():
    print("📦 正在创建 ZIP 包 ...")
    zip_file = zipfile.ZipFile(ZIP_NAME, "w", zipfile.ZIP_DEFLATED)

    for root, dirs, files in os.walk(".", topdown=True):
        # 排除 .git 目录
        if ".git" in dirs:
            dirs.remove(".git")

        for file in files:
            filepath = os.path.join(root, file)
            zip_path = filepath[2:] if filepath.startswith("./") else filepath
            zip_file.write(filepath, zip_path)

    zip_file.close()
    print(f"🎉 ZIP 已生成：{ZIP_NAME}")

if __name__ == "__main__":
    print("🚀 RapidOCR ZIP 打包工具启动")
    download_models()
    zip_project()
    print("✔ 完成！请在当前目录找到 math-ocr-full.zip")
