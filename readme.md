# Loudoun County Zoning Assistant

AI-powered Q&A system for zoning ordinances.

## Quick Start

1. Clone this repo
2. Copy `.env.example` to `.env` and add your OpenAI API key
3. Install dependencies: `pip install -r requirements.txt`
4. Upload a PDF: Place your zoning PDF in the root directory
5. Ingest the PDF: `python ingest.py`
6. Run the app: `python app.py`
7. Open browser to http://localhost:5000

## For Replit

This repo is designed to be imported directly into Replit.

1. Create new Repl → Import from GitHub
2. Add OPENAI_API_KEY to Secrets
3. Upload PDF via Replit file manager
4. Run ingest.py in Shell
5. Click Run

## Features

- Semantic search across zoning documents
- Citation of specific ordinance sections
- Usage tracking for analytics
- Multi-county support ready