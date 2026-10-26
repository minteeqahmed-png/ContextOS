"""Short-lived local OCR process, terminated on deadline by its parent."""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent/'.runtime'))
from extraction import extract_image_in_process

if __name__ == '__main__':
    print(json.dumps(extract_image_in_process(sys.stdin.read())))
