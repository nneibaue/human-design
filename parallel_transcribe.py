#!/usr/bin/env python3
"""Parallel transcription - transcribe a subset of files from a range"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from faster_whisper import WhisperModel

# Force unbuffered output for real-time logging
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Human Design terminology prompt to improve transcription accuracy
HD_PROMPT = """
Human Design lecture by Ra Uru Hu. Terms include: Manifestor, Generator, 
Manifesting Generator, Projector, Reflector, bodygraph, gates, channels, 
centers, defined, undefined, open centers, strategy, authority, sacral authority,
emotional authority, splenic authority, profile, incarnation cross, I Ching, 
hexagram, Rave cosmology, conditioning, not-self, deconditioning, aura, 
planetary imprint, Moon, Sun, Earth, nodes, design, personality, unconscious,
conscious, transit, penta, composite, definition, split definition, single definition,
triple split, quadruple split, no definition, lines, colors, tones, bases.
"""


def transcribe_file(model: WhisperModel, audio_path: Path, output_dir: Path) -> dict:
    """Transcribe a single audio file and save outputs"""
    
    print(f"\n{'='*60}")
    print(f"Transcribing: {audio_path.name}")
    print(f"{'='*60}")
    
    start_time = datetime.now()
    
    # Transcribe with VAD filtering and HD terminology prompt
    segments, info = model.transcribe(
        str(audio_path),
        beam_size=5,
        vad_filter=True,
        initial_prompt=HD_PROMPT,
    )
    
    # Collect segments
    all_segments = []
    full_text_lines = []
    
    for segment in segments:
        seg_data = {
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        }
        all_segments.append(seg_data)
        full_text_lines.append(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text.strip()}")
        print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text.strip()}")
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Prepare result
    result = {
        "file": audio_path.name,
        "path": str(audio_path),
        "language": info.language,
        "language_probability": info.language_probability,
        "duration_seconds": info.duration,
        "transcription_time_seconds": elapsed,
        "segments": all_segments
    }
    
    # Save outputs
    stem = audio_path.stem
    
    # Save JSON with metadata and timestamps
    json_path = output_dir / f"{stem}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Save plain text with timestamps
    txt_path = output_dir / f"{stem}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"# {audio_path.name}\n")
        f.write(f"# Language: {info.language} (confidence: {info.language_probability:.2%})\n")
        f.write(f"# Duration: {info.duration:.1f}s\n\n")
        f.write("\n".join(full_text_lines))
    
    print(f"\n✓ Completed in {elapsed:.1f}s")
    print(f"  Saved: {json_path.name}, {txt_path.name}")
    
    return result


def parallel_transcribe(audio_dir: Path, output_dir: Path, start_index: int = 0, count: int = None, model_name: str = "large-v3"):
    """Transcribe a range of audio files (MP3, M4A, WAV, etc.) for parallel processing"""

    # Find all audio files (MP3, M4A, WAV, OGG, FLAC, etc.)
    audio_extensions = ["*.mp3", "*.m4a", "*.wav", "*.ogg", "*.flac", "*.aac", "*.opus"]
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(audio_dir.glob(ext))

    audio_files = sorted(set(audio_files), key=lambda p: (len(p.stem), p.stem))

    if not audio_files:
        print(f"❌ No audio files found in {audio_dir}")
        print(f"   Supported formats: MP3, M4A, WAV, OGG, FLAC, AAC, Opus")
        return
    
    # Get the subset to process
    if count is None:
        count = len(audio_files)

    end_index = min(start_index + count, len(audio_files))
    files_to_process = audio_files[start_index:end_index]

    print(f"\n{'#'*60}")
    print(f"# PARALLEL TRANSCRIPTION")
    print(f"# Source: {audio_dir}")
    print(f"# Output: {output_dir}")
    print(f"# Processing files [{start_index+1}-{end_index}] of {len(audio_files)}")
    print(f"# Count: {len(files_to_process)}")
    print(f"# Model: {model_name} (CPU)")
    print(f"{'#'*60}")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load model
    print(f"\nLoading model: {model_name}...")
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    print("Model loaded!\n")
    
    total_start = datetime.now()
    
    for i, mp3_file in enumerate(files_to_process, 1):
        global_index = start_index + i
        print(f"\n[{global_index}/{len(mp3_files)}]", end="")
        
        try:
            transcribe_file(model, mp3_file, output_dir)
        except Exception as e:
            print(f"\n✗ Error transcribing {mp3_file.name}: {e}")
    
    total_elapsed = (datetime.now() - total_start).total_seconds()
    
    # Summary
    print(f"\n\n{'#'*60}")
    print(f"# WORKER COMPLETE")
    print(f"# Processed: {len(files_to_process)} files")
    print(f"# Time: {total_elapsed/60:.1f} minutes")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python parallel_transcribe.py <audio_directory> <output_directory> <start_index> [count] [model]")
        print("Example: python parallel_transcribe.py /audio/lecture /output/lecture 0 7 large-v3")
        sys.exit(1)
    
    audio_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    start_index = int(sys.argv[3])
    count = int(sys.argv[4]) if len(sys.argv) > 4 else None
    model_name = sys.argv[5] if len(sys.argv) > 5 else "large-v3"
    
    parallel_transcribe(audio_dir, output_dir, start_index, count, model_name)
