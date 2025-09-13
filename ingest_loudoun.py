#!/usr/bin/env python3
"""
Script to ingest the Loudoun County zoning ordinance PDF into ChromaDB
"""

import os
import sys
from ingest import ZoningIngester

def main():
    # Check if the PDF exists
    pdf_path = "loudoun_zoning_ordinance.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' not found!")
        sys.exit(1)
    
    print(f"Found PDF: {pdf_path}")
    print(f"File size: {os.path.getsize(pdf_path) / (1024*1024):.1f} MB")
    
    # Initialize the ingestion pipeline
    print("\nInitializing ingestion pipeline...")
    pipeline = ZoningIngester()
    
    # Ingest the PDF
    print("\nStarting ingestion process...")
    print("This may take a few minutes depending on the document size...")
    
    try:
        # The ingest_pdf method doesn't return a result, it prints progress
        pipeline.ingest_pdf(
            pdf_path=pdf_path,
            county="Loudoun"
        )
        
        print("\n✅ Ingestion completed successfully!")
        print("\n✨ You can now ask questions about the Loudoun County zoning ordinance through the web interface!")
        
    except Exception as e:
        print(f"\n❌ Error during ingestion: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()