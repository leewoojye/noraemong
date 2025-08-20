"""
Lyrics Synchronization Module
Aligns transcript/lyrics text with audio timestamps to create synchronized lyrics files.

This module takes an audio file and a transcript/lyrics file, then uses speech recognition
and text alignment algorithms to generate precise timestamps for each line of lyrics.
"""

import os
import time
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
import difflib
import re
from dataclasses import dataclass

# Audio processing and speech recognition
try:
    from faster_whisper import WhisperModel
    import torch
    import torchaudio
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please install: pip install faster-whisper torch torchaudio")
    raise

# Text processing
import unicodedata
from fuzzywuzzy import fuzz, process

@dataclass
class LyricSegment:
    """Represents a synchronized lyric segment with timing information."""
    start_time: float
    end_time: float
    text: str
    confidence: float = 0.0
    word_timings: Optional[List[Dict]] = None

class LyricsProcessor:
    """Handles lyrics/transcript file processing and normalization."""
    
    def __init__(self):
        self.line_separators = ['\n', '\r\n', '\r']
        
    def load_lyrics_file(self, file_path: str) -> List[str]:
        """
        Load lyrics from various file formats.
        
        Supports:
        - Plain text (.txt)
        - LRC files (.lrc) - extracts text only
        - SRT files (.srt) - extracts text only
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Lyrics file not found: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if file_path.suffix.lower() == '.lrc':
            return self._parse_lrc_text(content)
        elif file_path.suffix.lower() == '.srt':
            return self._parse_srt_text(content)
        else:
            return self._parse_plain_text(content)
    
    def _parse_plain_text(self, content: str) -> List[str]:
        """Parse plain text lyrics."""
        lines = content.split('\n')
        # Filter out empty lines and clean whitespace
        lyrics = [line.strip() for line in lines if line.strip()]
        return lyrics
    
    def _parse_lrc_text(self, content: str) -> List[str]:
        """Extract text from LRC format, ignoring timestamps."""
        lines = content.split('\n')
        lyrics = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Remove LRC timestamp format [mm:ss.xx]
            text = re.sub(r'\[\d+:\d+\.\d+\]', '', line).strip()
            if text:
                lyrics.append(text)
                
        return lyrics
    
    def _parse_srt_text(self, content: str) -> List[str]:
        """Extract text from SRT format, ignoring timestamps."""
        lines = content.split('\n')
        lyrics = []
        
        for line in lines:
            line = line.strip()
            # Skip sequence numbers, timestamps, and empty lines
            if (not line or 
                line.isdigit() or 
                '-->' in line):
                continue
            lyrics.append(line)
            
        return lyrics
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for better matching."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove punctuation but keep word boundaries
        text = re.sub(r'[^\w\s]', ' ', text)
        text = ' '.join(text.split())
        
        # Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)
        
        return text

class AudioTranscriber:
    """Handles audio transcription with word-level timestamps."""
    
    def __init__(self, model_size: str = "base", device: str = "auto"):
        """
        Initialize the transcriber.
        
        Args:
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large-v3")
            device: Device to use ("auto", "cpu", "cuda")
        """
        self.model_size = model_size
        self.device = device
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model."""
        print(f"📥 Loading Whisper model: {self.model_size}")
        try:
            self.model = WhisperModel(self.model_size, device=self.device)
            print("✅ Whisper model loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load Whisper model: {e}")
            raise
    
    def transcribe_with_timestamps(self, audio_path: str, language: Optional[str] = None) -> List[Dict]:
        """
        Transcribe audio with word-level timestamps.
        
        Returns:
            List of segments with detailed timing information
        """
        print(f"🎤 Transcribing audio: {Path(audio_path).name}")
        
        try:
            # Transcribe with word timestamps
            segments, info = self.model.transcribe(
                audio_path,
                beam_size=5,
                word_timestamps=True,
                language=language
            )
            
            # Convert to list and extract detailed information
            segment_list = []
            for segment in segments:
                segment_data = {
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text.strip(),
                    'words': []
                }
                
                # Extract word-level timestamps if available
                if hasattr(segment, 'words') and segment.words:
                    for word in segment.words:
                        word_data = {
                            'word': word.word.strip(),
                            'start': word.start,
                            'end': word.end,
                            'probability': getattr(word, 'probability', 0.0)
                        }
                        segment_data['words'].append(word_data)
                
                segment_list.append(segment_data)
            
            print(f"✅ Transcription complete: {len(segment_list)} segments")
            print(f"🌍 Detected language: {info.language} (confidence: {info.language_probability:.2f})")
            
            return segment_list
            
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            raise

class LyricsSynchronizer:
    """Main class for synchronizing lyrics with audio timestamps."""
    
    def __init__(self, model_size: str = "base", device: str = "auto"):
        """
        Initialize the synchronizer.
        
        Args:
            model_size: Whisper model size for transcription
            device: Device to use for processing
        """
        self.lyrics_processor = LyricsProcessor()
        self.transcriber = AudioTranscriber(model_size, device)
        
    def align_lyrics(self, audio_path: str, lyrics_path: str, 
                    language: Optional[str] = None,
                    similarity_threshold: float = 0.6) -> List[LyricSegment]:
        """
        Align lyrics with audio timestamps.
        
        Args:
            audio_path: Path to audio file
            lyrics_path: Path to lyrics/transcript file
            language: Language code for transcription (optional)
            similarity_threshold: Minimum similarity for text matching (0.0-1.0)
            
        Returns:
            List of synchronized lyric segments
        """
        print("🎵 Starting lyrics synchronization...")
        
        # Step 1: Load lyrics
        print("📖 Loading lyrics...")
        lyrics_lines = self.lyrics_processor.load_lyrics_file(lyrics_path)
        print(f"✅ Loaded {len(lyrics_lines)} lyric lines")
        
        # Step 2: Transcribe audio with timestamps
        print("🎤 Transcribing audio...")
        transcription_segments = self.transcriber.transcribe_with_timestamps(
            audio_path, language
        )
        
        # Step 3: Align lyrics with transcription
        print("🔄 Aligning lyrics with audio...")
        aligned_segments = self._align_text_with_timestamps(
            lyrics_lines, transcription_segments, similarity_threshold
        )
        
        print(f"✅ Synchronization complete: {len(aligned_segments)} segments aligned")
        return aligned_segments
    
    def _align_text_with_timestamps(self, lyrics_lines: List[str], 
                                   transcription_segments: List[Dict],
                                   similarity_threshold: float) -> List[LyricSegment]:
        """
        Align lyrics text with transcription timestamps using fuzzy matching.
        """
        aligned_segments = []
        
        # Normalize all text for better matching
        normalized_lyrics = [
            self.lyrics_processor.normalize_text(line) for line in lyrics_lines
        ]
        
        # Create a combined transcription text for global alignment
        transcription_text = " ".join([
            self.lyrics_processor.normalize_text(seg['text']) 
            for seg in transcription_segments
        ])
        
        # Track which transcription segments have been used
        used_segments = set()
        
        for i, (original_lyric, normalized_lyric) in enumerate(zip(lyrics_lines, normalized_lyrics)):
            best_match = None
            best_score = 0
            best_segment_indices = []
            
            # Try to find the best matching segment(s) for this lyric line
            for j, segment in enumerate(transcription_segments):
                if j in used_segments:
                    continue
                    
                normalized_segment = self.lyrics_processor.normalize_text(segment['text'])
                
                # Calculate similarity using multiple methods
                similarity_ratio = fuzz.ratio(normalized_lyric, normalized_segment) / 100.0
                partial_ratio = fuzz.partial_ratio(normalized_lyric, normalized_segment) / 100.0
                token_ratio = fuzz.token_sort_ratio(normalized_lyric, normalized_segment) / 100.0
                
                # Use the best similarity score
                score = max(similarity_ratio, partial_ratio, token_ratio)
                
                if score > best_score and score >= similarity_threshold:
                    best_score = score
                    best_match = segment
                    best_segment_indices = [j]
            
            # If no good single match, try combining adjacent segments
            if best_score < similarity_threshold:
                best_match, best_score, best_segment_indices = self._find_multi_segment_match(
                    normalized_lyric, transcription_segments, used_segments, similarity_threshold
                )
            
            # Create aligned segment
            if best_match and best_score >= similarity_threshold:
                # Mark segments as used
                for idx in best_segment_indices:
                    used_segments.add(idx)
                
                # Calculate timing
                if isinstance(best_match, list):
                    start_time = min(seg['start'] for seg in best_match)
                    end_time = max(seg['end'] for seg in best_match)
                    combined_words = []
                    for seg in best_match:
                        combined_words.extend(seg.get('words', []))
                else:
                    start_time = best_match['start']
                    end_time = best_match['end']
                    combined_words = best_match.get('words', [])
                
                aligned_segment = LyricSegment(
                    start_time=start_time,
                    end_time=end_time,
                    text=original_lyric,
                    confidence=best_score,
                    word_timings=combined_words
                )
                aligned_segments.append(aligned_segment)
                
                print(f"✓ Matched: '{original_lyric[:50]}...' (confidence: {best_score:.2f})")
            else:
                print(f"⚠️ No match found for: '{original_lyric[:50]}...'")
                # Add segment with estimated timing
                if aligned_segments:
                    estimated_start = aligned_segments[-1].end_time + 0.5
                    estimated_end = estimated_start + 3.0  # Default 3 second duration
                else:
                    estimated_start = 0.0
                    estimated_end = 3.0
                
                aligned_segment = LyricSegment(
                    start_time=estimated_start,
                    end_time=estimated_end,
                    text=original_lyric,
                    confidence=0.0
                )
                aligned_segments.append(aligned_segment)
        
        return aligned_segments
    
    def _find_multi_segment_match(self, target_lyric: str, transcription_segments: List[Dict],
                                 used_segments: set, similarity_threshold: float) -> Tuple[Optional[List[Dict]], float, List[int]]:
        """
        Try to match a lyric line with multiple consecutive transcription segments.
        """
        best_match = None
        best_score = 0
        best_indices = []
        
        # Try combining 2-4 consecutive segments
        for window_size in range(2, 5):
            for start_idx in range(len(transcription_segments) - window_size + 1):
                # Skip if any segment in window is already used
                if any(start_idx + i in used_segments for i in range(window_size)):
                    continue
                
                # Combine segments
                combined_segments = transcription_segments[start_idx:start_idx + window_size]
                combined_text = " ".join([
                    self.lyrics_processor.normalize_text(seg['text']) 
                    for seg in combined_segments
                ])
                
                # Calculate similarity
                similarity_ratio = fuzz.ratio(target_lyric, combined_text) / 100.0
                token_ratio = fuzz.token_sort_ratio(target_lyric, combined_text) / 100.0
                score = max(similarity_ratio, token_ratio)
                
                if score > best_score and score >= similarity_threshold:
                    best_score = score
                    best_match = combined_segments
                    best_indices = list(range(start_idx, start_idx + window_size))
        
        return best_match, best_score, best_indices

class OutputGenerator:
    """Generates various output formats for synchronized lyrics."""
    
    @staticmethod
    def save_as_lrc(segments: List[LyricSegment], output_path: str):
        """Save as LRC format."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("[ar:Generated by LyricsSynchronizer]\n")
            f.write(f"[ti:Synchronized Lyrics]\n")
            f.write(f"[by:AI Lyrics Sync]\n\n")
            
            for segment in segments:
                minutes = int(segment.start_time // 60)
                seconds = segment.start_time % 60
                timestamp = f"[{minutes:02d}:{seconds:05.2f}]"
                f.write(f"{timestamp}{segment.text}\n")
        
        print(f"💾 LRC file saved: {output_path}")
    
    @staticmethod
    def save_as_srt(segments: List[LyricSegment], output_path: str):
        """Save as SRT format."""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, 1):
                start_time = OutputGenerator._format_srt_time(segment.start_time)
                end_time = OutputGenerator._format_srt_time(segment.end_time)
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{segment.text}\n\n")
        
        print(f"💾 SRT file saved: {output_path}")
    
    @staticmethod
    def save_as_json(segments: List[LyricSegment], output_path: str):
        """Save as JSON format with detailed information."""
        data = {
            "metadata": {
                "generator": "LyricsSynchronizer",
                "version": "1.0",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_segments": len(segments)
            },
            "segments": []
        }
        
        for segment in segments:
            segment_data = {
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "duration": segment.end_time - segment.start_time,
                "text": segment.text,
                "confidence": segment.confidence
            }
            
            if segment.word_timings:
                segment_data["word_timings"] = segment.word_timings
            
            data["segments"].append(segment_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 JSON file saved: {output_path}")
    
    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """Format time for SRT format (HH:MM:SS,mmm)."""
        milliseconds = round(seconds * 1000.0)
        hours = milliseconds // 3_600_000
        milliseconds %= 3_600_000
        minutes = milliseconds // 60_000
        milliseconds %= 60_000
        secs = milliseconds // 1_000
        milliseconds %= 1_000
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    @staticmethod
    def print_alignment_summary(segments: List[LyricSegment]):
        """Print a summary of the alignment results."""
        total_segments = len(segments)
        high_confidence = sum(1 for seg in segments if seg.confidence >= 0.8)
        medium_confidence = sum(1 for seg in segments if 0.5 <= seg.confidence < 0.8)
        low_confidence = sum(1 for seg in segments if seg.confidence < 0.5)
        
        print("\n📊 Alignment Summary:")
        print(f"   Total segments: {total_segments}")
        print(f"   High confidence (≥80%): {high_confidence}")
        print(f"   Medium confidence (50-79%): {medium_confidence}")
        print(f"   Low confidence (<50%): {low_confidence}")
        
        if segments:
            total_duration = segments[-1].end_time - segments[0].start_time
            print(f"   Total duration: {total_duration:.1f} seconds")
            avg_confidence = sum(seg.confidence for seg in segments) / len(segments)
            print(f"   Average confidence: {avg_confidence:.2f}")

def sync_lyrics_to_audio(audio_path: str, lyrics_path: str, output_dir: str = "./sync_output",
                        model_size: str = "base", device: str = "auto", language: Optional[str] = None,
                        similarity_threshold: float = 0.6) -> Dict[str, str]:
    """
    Main function to sync lyrics with audio.
    
    Args:
        audio_path: Path to audio file
        lyrics_path: Path to lyrics/transcript file
        output_dir: Directory to save output files
        model_size: Whisper model size
        device: Processing device
        language: Language code (optional)
        similarity_threshold: Minimum similarity for matching
    
    Returns:
        Dictionary with paths to generated files
    """
    print("🎵 Lyrics Synchronization Started")
    print("=" * 50)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Initialize synchronizer
    synchronizer = LyricsSynchronizer(model_size=model_size, device=device)
    
    # Perform synchronization
    start_time = time.time()
    aligned_segments = synchronizer.align_lyrics(
        audio_path, lyrics_path, language, similarity_threshold
    )
    end_time = time.time()
    
    print(f"\n⏱️ Synchronization completed in {end_time - start_time:.2f} seconds")
    
    # Generate output filename base
    audio_name = Path(audio_path).stem
    output_base = output_path / f"{audio_name}_synced"
    
    # Save in multiple formats
    output_files = {}
    
    # LRC format (most common for synchronized lyrics)
    lrc_path = f"{output_base}.lrc"
    OutputGenerator.save_as_lrc(aligned_segments, lrc_path)
    output_files["lrc"] = lrc_path
    
    # SRT format (subtitle format)
    srt_path = f"{output_base}.srt"
    OutputGenerator.save_as_srt(aligned_segments, srt_path)
    output_files["srt"] = srt_path
    
    # JSON format (detailed data)
    json_path = f"{output_base}.json"
    OutputGenerator.save_as_json(aligned_segments, json_path)
    output_files["json"] = json_path
    
    # Print summary
    OutputGenerator.print_alignment_summary(aligned_segments)
    
    print(f"\n🎉 Synchronization complete! Files saved to: {output_dir}")
    return output_files

def main():
    """Command-line interface for lyrics synchronization."""
    parser = argparse.ArgumentParser(
        description="Synchronize lyrics with audio timestamps using AI speech recognition"
    )
    
    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument("lyrics_file", help="Path to lyrics/transcript file")
    parser.add_argument("--output_dir", default="./sync_output", 
                       help="Output directory for synchronized files")
    parser.add_argument("--model_size", default="base", 
                       choices=["tiny", "base", "small", "medium", "large-v3"],
                       help="Whisper model size")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"],
                       help="Device to use for processing")
    parser.add_argument("--language", default=None,
                       help="Language code (e.g., 'en', 'ko', 'es')")
    parser.add_argument("--similarity_threshold", type=float, default=0.6,
                       help="Minimum similarity threshold for text matching (0.0-1.0)")
    
    args = parser.parse_args()
    
    # Validate input files
    if not os.path.exists(args.audio_file):
        print(f"❌ Audio file not found: {args.audio_file}")
        return
    
    if not os.path.exists(args.lyrics_file):
        print(f"❌ Lyrics file not found: {args.lyrics_file}")
        return
    
    try:
        # Run synchronization
        output_files = sync_lyrics_to_audio(
            audio_path=args.audio_file,
            lyrics_path=args.lyrics_file,
            output_dir=args.output_dir,
            model_size=args.model_size,
            device=args.device,
            language=args.language,
            similarity_threshold=args.similarity_threshold
        )
        
        print(f"\n📁 Generated files:")
        for format_type, file_path in output_files.items():
            print(f"   {format_type.upper()}: {file_path}")
            
    except Exception as e:
        print(f"❌ Error during synchronization: {e}")
        raise

if __name__ == "__main__":
    main()