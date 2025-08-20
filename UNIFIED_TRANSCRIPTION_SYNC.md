# Unified Audio Transcription & Lyrics Synchronization

## Overview
Successfully combined the separate transcription and lyrics synchronization processes into one unified script that uses Whisper AI for both functions.

## Key Changes

### 1. Unified Script: `src/lyrics/transcribe_vocal.py`
- **Before**: Only basic audio transcription
- **After**: Dual-mode operation supporting both transcription and lyrics synchronization

### 2. New Functionality

#### Mode 1: Pure Transcription
```bash
python src/lyrics/transcribe_vocal.py audio_file.wav
```
- Transcribes audio using Whisper AI
- Generates word-level timestamps
- Outputs: .txt, .srt, .lrc, .json files

#### Mode 2: Lyrics Synchronization
```bash
python src/lyrics/transcribe_vocal.py audio_file.wav --lyrics_file lyrics.txt
```
- Loads existing lyrics from file (.txt, .lrc, .srt)
- Transcribes audio with word-level timestamps
- Aligns lyrics with audio using fuzzy text matching
- Provides confidence scores for alignment quality
- Outputs synchronized files with precise timing

### 3. Enhanced Features

#### Smart Text Matching
- Uses multiple similarity algorithms (ratio, partial ratio, token sort)
- Supports multi-segment matching for long lyric lines
- Configurable similarity threshold
- Handles mismatched or missing lyrics gracefully

#### Rich Output Formats
- **TXT**: Plain text transcript
- **SRT**: Subtitle format with timestamps
- **LRC**: Synchronized lyrics for music players
- **JSON**: Detailed metadata with word-level timings

#### Advanced Options
- Model size selection (tiny, base, small, medium, large-v3)
- Device selection (auto, cpu, cuda)
- Language specification
- Custom output directories
- Similarity threshold tuning

### 4. Technical Improvements

#### Unified Architecture
```python
class AudioTranscriber:
    - transcribe_with_timestamps()     # Pure transcription
    - align_lyrics_with_audio()        # Lyrics synchronization
    - _align_text_with_timestamps()    # Core alignment algorithm
    - _find_multi_segment_match()      # Multi-segment matching
```

#### Enhanced Data Structures
```python
@dataclass
class LyricSegment:
    start_time: float
    end_time: float
    text: str
    confidence: float
    word_timings: Optional[List[Dict]]
```

### 5. Performance Benefits

#### Efficiency Gains
- **Single Whisper model loading** instead of separate loads
- **Shared transcription process** for both modes
- **Optimized memory usage** with unified data structures
- **Reduced processing time** by eliminating duplicate operations

#### Quality Improvements
- **Word-level timestamps** provide precise synchronization
- **Confidence scoring** helps identify alignment quality
- **Multi-segment matching** handles complex lyric structures
- **Fuzzy matching** accommodates transcription variations

### 6. Usage Examples

#### Basic Transcription
```bash
python src/lyrics/transcribe_vocal.py song.wav --model_size base --device cpu
```

#### High-Quality Sync
```bash
python src/lyrics/transcribe_vocal.py song.wav \
  --lyrics_file lyrics.txt \
  --model_size large-v3 \
  --similarity_threshold 0.8 \
  --output_dir ./sync_output
```

#### Language-Specific Processing
```bash
python src/lyrics/transcribe_vocal.py korean_song.wav \
  --lyrics_file korean_lyrics.txt \
  --language ko \
  --model_size medium
```

### 7. Output Quality

#### Synchronization Statistics
The script provides detailed feedback:
- Total segments processed
- High/medium/low confidence alignment counts
- Average confidence score
- Total duration
- Processing time

#### Example Output
```
📊 동기화 결과 요약:
   전체 세그먼트: 114
   높은 신뢰도 (≥80%): 75
   중간 신뢰도 (50-79%): 28
   낮은 신뢰도 (<50%): 11
   전체 길이: 202.8초
   평균 신뢰도: 0.80
```

## Benefits of Unification

### 1. Simplified Workflow
- One command handles both transcription and synchronization
- Automatic mode detection based on presence of lyrics file
- Consistent output formats across both modes

### 2. Improved Accuracy
- Single transcription pass ensures consistency
- Word-level timestamps enable precise alignment
- Advanced matching algorithms handle variations

### 3. Better User Experience
- Clear progress indicators and status messages
- Detailed confidence reporting
- Graceful handling of alignment failures

### 4. Resource Efficiency
- Reduced memory footprint
- Faster processing time
- Single model loading

## Dependencies
All required packages are already in `requirements.txt`:
- faster-whisper (Whisper AI)
- fuzzywuzzy (text matching)
- python-Levenshtein (string similarity)

## Backward Compatibility
The unified script maintains full backward compatibility with existing transcription workflows while adding powerful new synchronization capabilities.
