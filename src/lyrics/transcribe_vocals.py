# transcribe_vocals.py

"""
Vocal Audio to Text Transcriber using OpenAI's Whisper

This script transcribes a given vocal audio file (e.g., MP3, WAV) into text
with high accuracy using the Whisper model via the Hugging Face transformers library.

It provides both a clean text output and a detailed subtitle file (.srt) with timestamps.
"""

# ⭐️ Usage: 터미널에 아래 형식으로 입력
# python transcribe_vocals.py ./karaoke_output/quality_test_vocals_clean.wav

# 속도 개선을 위한 --model 옵션:
# Medium 모델 (권장)
# python transcribe_vocals.py ./karaoke_output/quality_test_vocals_clean.wav --model "openai/whisper-medium"
# # Small 모델
# python transcribe_vocals.py ./karaoke_output/quality_test_vocals_clean.wav --model "openai/whisper-small"
# # Base 모델
# python transcribe_vocals.py ./karaoke_output/quality_test_vocals_clean.wav --model "openai/whisper-base"
# # Tiny 모델
# python transcribe_vocals.py ./karaoke_output/quality_test_vocals_clean.wav --model "openai/whisper-tiny"

import os
import torch
import subprocess
import warnings
from pathlib import Path
from argparse import ArgumentParser

# Suppress unnecessary warnings from Hugging Face
warnings.filterwarnings("ignore", category=UserWarning, module="transformers")

class VocalWhisperTranscriber:
    """
    A high-accuracy speech-to-text transcriber optimized for vocal tracks.
    """

    def __init__(self, model_name: str = "openai/whisper-large-v3", device: str = "auto"):
        """
        Initializes the transcriber with a specified Whisper model.

        Args:
            model_name (str): The name of the Whisper model to use from Hugging Face Hub.
            device (str): The device to run the model on ('auto', 'cpu', 'cuda', 'mps').
        """
        print("Initializing Vocal Transcriber...")
        self._check_ffmpeg()
        
        self.device = self._get_device(device)
        self.torch_dtype = torch.float16 if self.device.startswith("cuda") else torch.float32
        
        print(f"✅ Using device: {self.device.upper()} with data type: {self.torch_dtype}")

        try:
            from transformers import pipeline
            print(f"📦 Loading model '{model_name}'... (This may take a while for the first time)")
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=model_name,
                torch_dtype=self.torch_dtype,
                device=self.device,
            )
            print("✅ Model loaded successfully!")
        except ImportError:
            print("\n❌ Error: 'transformers' or 'accelerate' not found.")
            print("Please install them using: pip install transformers accelerate torch")
            exit(1)
        except Exception as e:
            print(f"\n❌ Failed to load the model: {e}")
            print("Please check your internet connection and dependencies.")
            exit(1)

    def _get_device(self, device: str) -> str:
        """Determines the best available hardware device."""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
            return "cpu"
        return device

    def _check_ffmpeg(self):
        """Checks if FFmpeg is installed and available in the system's PATH."""
        try:
            subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("\n⚠️ Warning: FFmpeg is not found in your system's PATH.")
            print("FFmpeg is required to process various audio formats like MP3.")
            print("Please install it and ensure it's accessible from your terminal.")
            # Depending on the strictness, you might want to exit here.
            # For now, we'll just warn the user.

    def transcribe(self, audio_file_path: str) -> dict:
        """
        Transcribes the audio file and returns the text with timestamps.

        Args:
            audio_file_path (str): The path to the input audio file.

        Returns:
            A dictionary containing the full text and chunked data with timestamps.
        """
        if not Path(audio_file_path).is_file():
            raise FileNotFoundError(f"Audio file not found at: {audio_file_path}")

        print(f"\n🎵 Starting transcription for: {audio_file_path}")
        
        # Using generate_kwargs for language specification can improve accuracy
        outputs = self.pipe(
            audio_file_path,
            chunk_length_s=30,
            batch_size=4,
            return_timestamps=True,
            # 언어자동감지를 위한 옵션제거
            # generate_kwargs={"language": "korean"} # Process as Korean
        )
        
        print("✅ Transcription complete!")
        return outputs
        
    @staticmethod
    def save_results(transcription_data: dict, output_basename: str):
        """
        Saves the transcription results into a .txt and a .srt file.

        Args:
            transcription_data (dict): The output from the transcription process.
            output_basename (str): The base name for the output files (without extension).
        """
        # Save as plain text (.txt)
        txt_path = f"{output_basename}.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(transcription_data['text'])
        print(f"📄 Full text saved to: {txt_path}")
        
        # Save as subtitle file (.srt)
        srt_path = f"{output_basename}.srt"
        with open(srt_path, 'w', encoding='utf-8') as f:
            for i, chunk in enumerate(transcription_data['chunks']):
                start_time = chunk['timestamp'][0]
                end_time = chunk['timestamp'][1]
                
                # Format to SRT time format: HH:MM:SS,ms
                start_srt = f"{int(start_time // 3600):02}:{int((start_time % 3600) // 60):02}:{int(start_time % 60):02},{int((start_time % 1) * 1000):03}"
                end_srt = f"{int(end_time // 3600):02}:{int((end_time % 3600) // 60):02}:{int(end_time % 60):02},{int((end_time % 1) * 1000):03}"
                
                text = chunk['text'].strip()
                
                f.write(f"{i + 1}\n")
                f.write(f"{start_srt} --> {end_srt}\n")
                f.write(f"{text}\n\n")
        print(f"🎬 Subtitle file with timestamps saved to: {srt_path}")


def main():
    """Main function to run the script from the command line."""
    parser = ArgumentParser(description="Transcribe a vocal audio file to text using OpenAI's Whisper.")
    parser.add_argument("audio_file", type=str, help="Path to the audio file to transcribe (e.g., my_vocals.mp3).")
    parser.add_argument(
        "--model", 
        type=str, 
        default="openai/whisper-large-v3", 
        help="Whisper model name (e.g., 'openai/whisper-medium', 'openai/whisper-base')."
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        choices=["auto", "cpu", "cuda", "mps"],
        help="Device to use for computation."
    )
    
    args = parser.parse_args()

    try:
        # Initialize the transcriber
        transcriber = VocalWhisperTranscriber(model_name=args.model, device=args.device)
        
        # Perform transcription
        result_data = transcriber.transcribe(args.audio_file)
        
        # Save the results
        # output_basename = Path(args.audio_file).stem
        # transcriber.save_results(result_data, output_basename)
        output_dir = "./karaoke_output"
        os.makedirs(output_dir, exist_ok=True)
        output_basename = os.path.join(output_dir, Path(args.audio_file).stem)
        transcriber.save_results(result_data, output_basename)
        
        print("\n🎉 All tasks completed successfully!")

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()