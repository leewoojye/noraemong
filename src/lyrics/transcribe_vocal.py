# transcribe_fast.py

import time
from pathlib import Path
import argparse
from faster_whisper import WhisperModel

def format_time(seconds: float) -> str:
    """초를 SRT 타임스탬프 형식(HH:MM:SS,ms)으로 변환합니다."""
    milliseconds = round(seconds * 1000.0)
    hours = milliseconds // 3_600_000
    milliseconds %= 3_600_000
    minutes = milliseconds // 60_000
    milliseconds %= 60_000
    seconds = milliseconds // 1_000
    milliseconds %= 1_000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def save_as_srt(segments: list, output_path: Path):
    """추출된 세그먼트를 .srt 자막 파일 형식으로 저장합니다."""
    with open(output_path, 'w', encoding='utf-8') as srt_file:
        for i, segment in enumerate(segments):
            start = format_time(segment.start)
            end = format_time(segment.end)
            text = segment.text.strip()
            
            srt_file.write(f"{i + 1}\n")
            srt_file.write(f"{start} --> {end}\n")
            srt_file.write(f"{text}\n\n")
    print(f"🎬 SRT 자막 파일 저장 완료: {output_path}")

def save_as_txt(segments: list, output_path: Path):
    """추출된 텍스트를 .txt 파일 형식으로 저장합니다."""
    with open(output_path, 'w', encoding='utf-8') as txt_file:
        for segment in segments:
            txt_file.write(segment.text.strip() + "\n")
    print(f"📄 일반 텍스트 파일 저장 완료: {output_path}")

def transcribe_vocal():
    parser = argparse.ArgumentParser(description="faster-whisper를 사용하여 오디오 파일에서 텍스트를 추출합니다.")
    parser.add_argument("audio_file", type=str, help="텍스트를 추출할 오디오 파일 경로")
    parser.add_argument("--model_size", type=str, default="large-v3", help="사용할 Whisper 모델 크기 (예: tiny, base, small, medium, large-v3)")
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cpu", "cuda"], help="사용할 장치 (auto, cpu, cuda)")
    parser.add_argument("--compute_type", type=str, default="default", choices=["default", "int8", "float16"], help="연산 타입 (메모리 및 속도 최적화)")
    parser.add_argument("--language", type=str, default=None, help="오디오의 언어 코드 (예: ko, en). 지정 시 언어 감지 과정을 생략하여 더 빠름.")
    
    args = parser.parse_args([
        "./data/input/quality_test_vocals_clean.wav",
        "--model_size", "base",
        "--device", "cpu",
        "--compute_type", "int8",
    ])

    audio_path = Path(args.audio_file)
    if not audio_path.exists():
        print(f"❌ 오류: 파일을 찾을 수 없습니다 -> {audio_path}")
        return

    print("="*50)
    print(f"🚀 텍스트 추출 시작: {audio_path.name}")
    print(f"모델: {args.model_size}, 장치: {args.device}, 연산 타입: {args.compute_type}")
    print("="*50)

    try:
        # 모델 로드
        model = WhisperModel(args.model_size, device=args.device, compute_type=args.compute_type)
        
        # 텍스트 추출 실행
        start_time = time.perf_counter()
        
        segments, info = model.transcribe(str(audio_path), beam_size=5, language=args.language)
        
        # faster-whisper의 결과는 제너레이터이므로 리스트로 변환하여 사용
        segment_list = list(segments)
        
        end_time = time.perf_counter()
        
        print(f"✅ 텍스트 추출 완료! (소요 시간: {end_time - start_time:.2f}초)")
        print(f"감지된 언어: '{info.language}' (확률: {info.language_probability:.2f})")
        
        # 결과 저장
        output_basename = audio_path.parent / audio_path.stem # 파일 경로와 확장자를 합치는 연산
        save_as_txt(segment_list, output_basename.with_suffix(".txt"))
        save_as_srt(segment_list, output_basename.with_suffix(".srt"))

    except Exception as e:
        print(f"❌ 오류 발생: {e}")