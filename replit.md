# Loudoun County Zoning Assistant

## Overview

This is an AI-powered Q&A system for zoning ordinances, specifically designed for Loudoun County. The application allows users to ask natural language questions about zoning codes and receives intelligent answers backed by semantic search through the actual ordinance documents. The system uses vector embeddings to find relevant sections of zoning documents and leverages OpenAI's GPT models to provide contextual answers with proper citations.

## User Preferences

Preferred communication style: Simple, everyday language.

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