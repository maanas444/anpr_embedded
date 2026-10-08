# ANPR
Automatic Number Plate Recognition system for ENSE810 - Embedded Software Engineering

## Setup
### General setup (Linux):
```
python3 -m venv .venv
source .venv/bin/activate
```

### Node setup:
```
sudo apt update
sudo apt install swig build-essential -y
sudo apt install tesseract-ocr -y
pip install --extra-index-url https://download.pytorch.org/whl/cpu torch torchvision
pip install -e .[node]
```

### Server setup:
```
pip install -e .[server]
```

### How to exit virtual environment:
```
deactivate
```

## How to use (Custom commands)
The project is split over two Raspberry Pi's

### Start commands
Camera Node:
```
node
```

Server:
```
server
```
