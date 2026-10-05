import os
import platform
import subprocess
import sys


def has_tesseract_installed_successfully() -> bool:
    # Returns the file path to 'tesseract' if found in PATH, otherwise None
    return shutil.which("tesseract") is not None

# Courtesy of Gemini
def install():
    system = platform.system().lower()
    print(f"Detected OS: {system}")

    try:
        if system == "linux":
            print("Installing tesseract-ocr via apt...")
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "tesseract-ocr"], check=True)

        elif system == "darwin":  # macOS
            print("Installing tesseract via Homebrew...")
            subprocess.run(["brew", "install", "tesseract"], check=True)

        elif system == "windows":
            print("Installing tesseract via winget...")
            subprocess.run(["winget", "install", "UB-Mannheim.TesseractOCR"], check=True)

        else:
            print(f"Unsupported operating system: {system}")
            sys.exit(1)

        print("\nTesseract OCR installation completed successfully!")

    except subprocess.CalledProcessError as e:
        print(f"\nFailed to install Tesseract: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install()
