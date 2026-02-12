"""MCP Server for Ra Uru Hu Transcription Pipeline

This server provides tools for:
- Discovering and listing Ra lecture series from ~/HD/AUDIO
- Queuing transcription jobs with parallel worker coordination
- Tracking transcription progress and status
- Indexing completed transcripts into ra_transcripts/index.json
- Searching indexed transcripts by keyword (BM25)
- Retrieving specific transcript content
"""

__version__ = "0.1.0"
