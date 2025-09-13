# Loudoun County Planning Staff Assistant (B2G)

## Overview

This is a dual-mode zoning compliance system for Loudoun County:

**PUBLIC MODE**: A self-service compliance checker with TurboTax-style guided experience that helps residents check BEFORE they build, plant, or change property use. Features plain English interface, color-coded answers (Green/Yellow/Red), and mobile-first design.

**STAFF MODE**: A professional B2G tool for county planning staff with full citation chains, parcel awareness, audit logging, precedent search, and official determination exports. 

Both modes share the same RAG backend using vector embeddings to search through 548 sections of the current Loudoun County Zoning Ordinance, powered by OpenAI's GPT models.

## User Preferences

Preferred communication style: Simple, everyday language.

## Staff Login Credentials (Demo)

- **John Smith (Planning)**: jsmith / planning2024
- **Mary Jones (Zoning)**: mjones / zoning2024
- **Robert Lopez (Staff)**: rlopez / staff2024
- **Admin**: admin / admin2024

## System Architecture

### Frontend Architecture
- **Technology**: Simple HTML/CSS/JavaScript with Flask templating
- **Design**: Single-page application with a clean, government-friendly interface
- **Interaction Model**: Synchronous Q&A with real-time responses

### Backend Architecture
- **Framework**: Flask web application with RESTful API endpoints
- **Core Components**:
  - `app.py`: Main Flask application with routes for querying and health checks
  - `query_engine.py`: Handles semantic search and answer generation
  - `ingest.py`: Processes PDF documents and creates vector embeddings
- **Design Pattern**: Modular architecture separating ingestion, querying, and web interface concerns

### Data Storage Solutions
- **Vector Database**: ChromaDB for storing document embeddings and metadata
- **Storage Mode**: Persistent local storage in `./chroma_data` directory
- **Document Processing**: PDF parsing with smart chunking that respects section boundaries
- **Embedding Strategy**: OpenAI's text-embedding-3-small model for semantic search

### Search and Retrieval System
- **Search Method**: Semantic vector search using cosine similarity
- **Chunking Strategy**: Intelligent text segmentation that preserves document structure
- **Citation System**: Maintains metadata for proper source attribution
- **Multi-county Support**: Architecture ready for expansion beyond Loudoun County

### AI Integration
- **Primary Model**: OpenAI GPT models for answer generation
- **Embedding Model**: OpenAI text-embedding-3-small for document vectorization
- **Processing Pipeline**: Query → Embedding → Similarity Search → Context Assembly → Answer Generation

### Usage Tracking
- **Analytics**: In-memory logging of queries and timestamps
- **Health Monitoring**: Basic health check endpoint with query statistics
- **County Tracking**: Prepared for multi-jurisdiction analytics

## External Dependencies

### AI Services
- **OpenAI API**: Core dependency for both embeddings and text generation
  - Text embeddings for semantic search
  - GPT models for answer generation
  - Requires API key configuration

### Database and Storage
- **ChromaDB**: Vector database for storing and searching document embeddings
  - Local persistent storage
  - HNSW indexing for efficient similarity search
  - Cosine similarity metric

### Document Processing
- **PyPDF2**: PDF parsing and text extraction
- **tiktoken**: Token counting for OpenAI models
- **networkx**: Graph processing capabilities (imported but usage unclear from visible code)

### Web Framework
- **Flask**: Lightweight web framework for API and web interface
- **Standard Python libraries**: datetime, json, os, hashlib for basic operations

### Development and Deployment
- **python-dotenv**: Environment variable management
- **Replit Platform**: Designed for easy deployment and sharing
- **Environment Requirements**: Python 3.x with pip package management