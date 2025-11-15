# Tag Extractor

A Python script that extracts tags from user prompts using PydanticAI and OpenAI.

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key as an environment variable:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Method 1: Pass prompt as command line arguments
```bash
python tag_extractor.py "Create a presentation about machine learning and artificial intelligence"
```

### Method 2: Pipe input from stdin
```bash
echo "Create a presentation about machine learning and artificial intelligence" | python tag_extractor.py
```

### Method 3: Interactive input
```bash
python tag_extractor.py
# Then type your prompt and press Ctrl+D (Unix) or Ctrl+Z (Windows)
```

## Example Output

```
Processing prompt: Create a presentation about machine learning and artificial intelligence
Extracting tags...

Extracted tags:
  - machine learning
  - artificial intelligence
  - presentation
  - technology
```

