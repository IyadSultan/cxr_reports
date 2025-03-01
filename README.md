# Chest X-Ray Reports Classification

A Python-based tool that uses OpenAI's GPT-3.5-turbo model to classify chest X-ray reports into three categories:
- **0**: Normal
- **1**: Abnormal
- **2**: Uncertain OR reports mentioning lines, catheters, or tubes

## Project Description

This project processes radiology reports from an Excel file and uses OpenAI's GPT-3.5-turbo model to classify each report based on its content. The classification adds a new column to the Excel file.

## Requirements

- Python 3.8+
- OpenAI API key
- Dependencies listed in requirements.txt

## Setup

1. Create a virtual environment using uv:
   ```
   uv venv
   ```

2. Activate the virtual environment:
   ```
   # On Windows
   .\venv\Scripts\activate
   
   # On Unix/Mac
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   uv pip install -r requirements.txt
   ```

4. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

1. Test with a small sample first:
   ```
   python test_extractor.py
   ```
   
   This will run both direct API tests and tests using the main extractor function.

2. Run the full classification:
   ```
   python extractor.py
   ```

The script will create:
- `radiology_classified.xlsx`: Excel file with the classification results
- `extractor_log.log`: Log file with processing details

## Features

- Processes reports in batches with frequent saving (every 5 reports)
- Comprehensive logging with both file and console output
- Resumes processing from where it left off if interrupted
- Rate limiting to avoid OpenAI API limits
- Robust error handling with retry mechanism
- Intelligent extraction of classification values
- Handles API failures gracefully

## Project Status

See [project_status.md](project_status.md) for current progress and upcoming tasks. 