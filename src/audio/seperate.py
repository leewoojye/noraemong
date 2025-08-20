"""
Karaoke Audio Separator - Using Facebook's Demucs
Step 1: Professional-grade Vocal/Instrumental Separation

This module uses Facebook's Demucs model for high-quality music source separation,
specifically optimized for karaoke applications.
"""

import os
import torch
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, Union
import logging
import subprocess
import sys
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DemucsInstaller:
    """Handles Demucs installation and setup."""
    
    @staticmethod
    def install_demucs():
        """Install Demucs and dependencies."""
        try:
            import demucs
            logger.info("✅ Demucs already installed")
            return True
        except ImportError:
            logger.info("📦 Installing Demucs...")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", 
                    "demucs", "torch", "torchaudio"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info("✅ Demucs installed successfully")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to install Demucs: {e}")
                return False
    
    @staticmethod
    def check_dependencies():
        """Check if all required dependencies are available."""
        required = ['torch', 'torchaudio', 'demucs']
        missing = []
        
        for package in required:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        if missing:
            logger.warning(f"Missing packages: {missing}")
            return False
        return True

class AudioProcessor:
    """Handles audio I/O operations optimized for Demucs."""
    
    @staticmethod
    def load_audio(file_path: str, sample_rate: int = 44100) -> Tuple[torch.Tensor, int]:
        """
        Load audio file and convert to Demucs-compatible format.
        
        Returns:
            Tuple of (audio_tensor, sample_rate)
            audio_tensor shape: [channels, samples]
        """
        try:
            # Load with librosa
            audio, sr = librosa.load(file_path, sr=sample_rate, mono=False, dtype=np.float32)
            
            # Ensure stereo [2, samples]
            if audio.ndim == 1:
                audio = np.stack([audio, audio])
            elif audio.shape[0] == 1:
                audio = np.stack([audio[0], audio[0]])
            elif audio.shape[0] > 2:
                audio = audio[:2]
            
            # Convert to torch tensor
            audio_tensor = torch.from_numpy(audio).float()
            
            logger.info(f"Loaded audio: {audio_tensor.shape} at {sr}Hz, duration: {audio_tensor.shape[1]/sr:.2f}s")
            return audio_tensor, sr
            
        except Exception as e:
            logger.error(f"Error loading audio {file_path}: {e}")
            raise
    
    @staticmethod
    def save_audio(audio: Union[torch.Tensor, np.ndarray], file_path: str, sample_rate: int = 44100):
        """Save audio tensor/array to file."""
        try:
            # Convert to numpy if needed
            if isinstance(audio, torch.Tensor):
                audio = audio.detach().cpu().numpy()
            
            # Ensure correct format [samples, channels] for soundfile
            if audio.ndim == 2 and audio.shape[0] == 2:
                audio = audio.T  # [2, samples] -> [samples, 2]
            elif audio.ndim == 1:
                audio = np.stack([audio, audio], axis=1)
                
            # Normalize to prevent clipping
            max_val = np.max(np.abs(audio))
            if max_val > 1.0:
                audio = audio / max_val * 0.98
                
            sf.write(file_path, audio, sample_rate, subtype='PCM_24')
            logger.info(f"Saved: {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving audio to {file_path}: {e}")
            raise

class DemucsKaraokeSeparator:
    """
    Demucs-based separator optimized for karaoke applications.
    """
    
    def __init__(self, model_name: str = "htdemucs", device: str = "auto", shifts: int = 1):
        """
        Initialize Demucs separator.
        
        Args:
            model_name: Demucs model to use ("htdemucs", "htdemucs_ft", "mdx_extra", "mdx_extra_q")
            device: Device to use ("auto", "cpu", "cuda", "mps")  
            shifts: Number of random shifts for better quality (1-10, higher=better but slower)
        """
        # Ensure Demucs is installed
        if not DemucsInstaller.check_dependencies():
            if not DemucsInstaller.install_demucs():
                raise RuntimeError("Failed to install Demucs dependencies")
        
        self.model_name = model_name
        self.shifts = shifts
        self.device = self._get_device(device)
        self.model = None
        self.sample_rate = 44100
        
        # Load model
        self._load_model()
        
    def _get_device(self, device: str) -> str:
        """Determine the best available device with MPS fallback."""
        if device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
                logger.info("🚀 Using CUDA acceleration")
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                # MPS has known issues with large operations, use CPU for stability
                device = "cpu"
                logger.info("💻 Using CPU (MPS has compatibility issues with Demucs)")
            else:
                device = "cpu"
                logger.info("💻 Using CPU")
        else:
            logger.info(f"🔧 Using specified device: {device}")
        
        return device
    
    def _load_model(self):
        """Load the Demucs model."""
        try:
            from demucs.pretrained import get_model
            
            logger.info(f"📥 Loading Demucs model: {self.model_name}")
            
            # Load the pretrained model
            self.model = get_model(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            # Get source names (usually ['drums', 'bass', 'other', 'vocals'])
            self.sources = self.model.sources
            self.vocal_index = self.sources.index('vocals') if 'vocals' in self.sources else -1
            
            logger.info(f"✅ Model loaded successfully")
            logger.info(f"🎵 Separates into: {self.sources}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load Demucs model: {e}")
            raise
    
    def separate(self, audio: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Separate audio using Demucs with enhanced error handling.
        
        Args:
            audio: Input audio tensor [channels, samples]
            
        Returns:
            Dictionary mapping source names to separated audio tensors
        """
        try:
            from demucs.apply import apply_model
            
            logger.info("🎵 Starting Demucs separation...")
            
            # Force CPU for MPS compatibility issues
            if self.device == "mps":
                logger.info("⚠️ Switching to CPU due to MPS limitations")
                self.device = "cpu"
                self.model = self.model.cpu()
            
            # Ensure audio is on correct device and proper format
            audio = audio.to(self.device)
            
            # Limit audio length for memory efficiency (process in chunks if needed)
            max_duration = 300  # 5 minutes max per chunk
            sample_rate = 44100
            max_samples = max_duration * sample_rate
            
            if audio.shape[1] > max_samples:
                logger.info(f"⚠️ Long audio detected ({audio.shape[1]/sample_rate:.1f}s), processing in chunks...")
                return self._process_long_audio(audio, max_samples)
            
            # Add batch dimension: [batch, channels, samples]
            if audio.dim() == 2:
                audio = audio.unsqueeze(0)
            
            # Apply the model with conservative settings for stability
            with torch.no_grad():
                try:
                    sources = apply_model(
                        self.model, 
                        audio, 
                        shifts=min(self.shifts, 1),  # Reduce shifts for stability
                        split=True,  # Process in chunks to save memory
                        overlap=0.1,  # Reduce overlap for memory efficiency
                        device=self.device
                    )[0]  # Remove batch dimension
                except RuntimeError as e:
                    if "MPS" in str(e) or "channels" in str(e):
                        logger.warning("⚠️ MPS error detected, falling back to CPU...")
                        self.device = "cpu"
                        self.model = self.model.cpu()
                        audio = audio.cpu()
                        sources = apply_model(
                            self.model, 
                            audio, 
                            shifts=1,  # Minimal shifts for CPU
                            split=True,
                            overlap=0.1,
                            device=self.device
                        )[0]
                    else:
                        raise
            
            # Create dictionary mapping source names to tensors
            separated = {}
            for i, source_name in enumerate(self.sources):
                separated[source_name] = sources[i]
            
            logger.info("✅ Separation completed successfully")
            return separated
            
        except Exception as e:
            logger.error(f"❌ Demucs separation failed: {e}")
            raise
    
    def _process_long_audio(self, audio: torch.Tensor, chunk_size: int) -> Dict[str, torch.Tensor]:
        """Process long audio files in chunks to avoid memory issues."""
        from demucs.apply import apply_model
        
        total_samples = audio.shape[1]
        overlap_samples = chunk_size // 10  # 10% overlap
        
        # Initialize output tensors
        separated = {source: torch.zeros_like(audio) for source in self.sources}
        
        start = 0
        chunk_num = 1
        total_chunks = (total_samples + chunk_size - overlap_samples - 1) // (chunk_size - overlap_samples)
        
        while start < total_samples:
            end = min(start + chunk_size, total_samples)
            logger.info(f"Processing chunk {chunk_num}/{total_chunks} ({start/44100:.1f}s - {end/44100:.1f}s)")
            
            # Extract chunk
            audio_chunk = audio[:, start:end]
            if audio_chunk.dim() == 2:
                audio_chunk = audio_chunk.unsqueeze(0)
            
            # Process chunk
            with torch.no_grad():
                sources_chunk = apply_model(
                    self.model,
                    audio_chunk,
                    shifts=1,  # Minimal shifts for chunks
                    split=True,
                    overlap=0.1,
                    device=self.device
                )[0]
            
            # Add to output with overlap handling
            chunk_start = start
            chunk_end = min(end, total_samples)
            
            for i, source_name in enumerate(self.sources):
                if start == 0:
                    # First chunk - use everything
                    separated[source_name][:, chunk_start:chunk_end] = sources_chunk[i][:, :chunk_end-chunk_start]
                else:
                    # Subsequent chunks - blend overlap region
                    overlap_start = max(0, overlap_samples)
                    separated[source_name][:, chunk_start+overlap_start:chunk_end] = sources_chunk[i][:, overlap_start:chunk_end-chunk_start]
            
            start += chunk_size - overlap_samples
            chunk_num += 1
        
        return separated
    
    def create_karaoke_track(self, separated_sources: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Create clean karaoke instrumental track by combining non-vocal sources.
        
        Args:
            separated_sources: Dictionary of separated sources
            
        Returns:
            Karaoke instrumental track tensor
        """
        # Combine all non-vocal sources
        instrumental = torch.zeros_like(separated_sources['vocals'])
        
        for source_name, source_audio in separated_sources.items():
            if source_name != 'vocals':
                instrumental += source_audio
        
        return instrumental

class VocalEnhancer:
    """
    Post-processes separated vocals to remove background music bleed.
    """
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        
    def enhance_vocals(self, vocals: torch.Tensor, instrumental: torch.Tensor, 
                      original_mix: torch.Tensor) -> torch.Tensor:
        """
        Clean up vocals by removing instrumental bleed.
        
        Args:
            vocals: Raw vocal track from Demucs
            instrumental: Instrumental track 
            original_mix: Original audio mix
            
        Returns:
            Enhanced vocal track with reduced background music
        """
        logger.info("🎤 Enhancing vocal clarity...")
        
        # Convert to numpy for processing
        vocals_np = vocals.detach().cpu().numpy()
        instrumental_np = instrumental.detach().cpu().numpy()
        original_np = original_mix.detach().cpu().numpy()
        
        # Method 1: Spectral subtraction of instrumental bleed
        vocals_cleaned = self._spectral_vocal_cleanup(vocals_np, instrumental_np)
        
        # Method 2: Dynamic range enhancement for vocals
        vocals_enhanced = self._enhance_vocal_dynamics(vocals_cleaned)
        
        # Method 3: Frequency-based vocal isolation
        vocals_isolated = self._frequency_vocal_isolation(vocals_enhanced)
        
        # Method 4: Adaptive noise reduction
        vocals_final = self._adaptive_noise_reduction(vocals_isolated, instrumental_np)
        
        logger.info("✅ Vocal enhancement completed")
        return torch.from_numpy(vocals_final).float()
    
    def _spectral_vocal_cleanup(self, vocals: np.ndarray, instrumental: np.ndarray) -> np.ndarray:
        """Remove instrumental bleed using spectral subtraction."""
        # Work with mono for analysis
        vocals_mono = vocals.mean(axis=0) if vocals.shape[0] == 2 else vocals
        inst_mono = instrumental.mean(axis=0) if instrumental.shape[0] == 2 else instrumental
        
        # Convert to frequency domain
        vocals_stft = librosa.stft(vocals_mono, n_fft=2048, hop_length=512)
        inst_stft = librosa.stft(inst_mono, n_fft=2048, hop_length=512)
        
        # Calculate spectral subtraction mask
        vocals_mag = np.abs(vocals_stft)
        inst_mag = np.abs(inst_stft)
        
        # Create adaptive mask to suppress instrumental bleed
        # Where instrumental is strong relative to vocals, reduce vocals
        ratio = inst_mag / (vocals_mag + 1e-10)
        suppression_mask = 1.0 / (1.0 + ratio * 0.5)  # Adaptive suppression
        
        # Apply frequency-dependent enhancement
        freqs = librosa.fft_frequencies(sr=self.sample_rate, n_fft=2048)
        for i, freq in enumerate(freqs):
            if 200 <= freq <= 3000:  # Core vocal range - preserve more
                suppression_mask[i] = np.maximum(suppression_mask[i], 0.7)
            elif freq < 100 or freq > 8000:  # Outside vocal range - suppress more
                suppression_mask[i] *= 0.3
        
        # Apply mask and convert back
        vocals_clean_stft = vocals_stft * suppression_mask
        vocals_clean_mono = librosa.istft(vocals_clean_stft, hop_length=512)
        
        # Convert back to stereo if needed
        if vocals.shape[0] == 2:
            return np.stack([vocals_clean_mono, vocals_clean_mono])
        return vocals_clean_mono
    
    def _enhance_vocal_dynamics(self, vocals: np.ndarray) -> np.ndarray:
        """Enhance vocal dynamics and presence."""
        # Apply gentle compression to bring out quiet vocal parts
        vocals_compressed = np.sign(vocals) * np.power(np.abs(vocals) + 1e-10, 0.7)
        
        # Apply gentle high-pass filter to remove low-frequency rumble
        from scipy import signal
        sos = signal.butter(4, 80, btype='high', fs=self.sample_rate, output='sos')
        vocals_filtered = signal.sosfilt(sos, vocals_compressed, axis=-1)
        
        return vocals_filtered
    
    def _frequency_vocal_isolation(self, vocals: np.ndarray) -> np.ndarray:
        """Isolate vocal frequencies and reduce non-vocal content."""
        vocals_mono = vocals.mean(axis=0) if vocals.shape[0] == 2 else vocals
        
        # Use harmonic/percussive separation to isolate vocal-like content
        vocals_harmonic, vocals_percussive = librosa.effects.hpss(vocals_mono, margin=4.0)
        
        # Vocals are primarily harmonic, reduce percussive content
        vocals_isolated = vocals_harmonic + vocals_percussive * 0.2
        
        # Convert back to stereo if needed
        if vocals.shape[0] == 2:
            return np.stack([vocals_isolated, vocals_isolated])
        return vocals_isolated
    
    def _adaptive_noise_reduction(self, vocals: np.ndarray, instrumental: np.ndarray) -> np.ndarray:
        """Apply adaptive noise reduction based on instrumental content."""
        # Work with mono
        vocals_mono = vocals.mean(axis=0) if vocals.shape[0] == 2 else vocals
        inst_mono = instrumental.mean(axis=0) if instrumental.shape[0] == 2 else instrumental
        
        # Compute short-time energy
        frame_length = 2048
        hop_length = 512
        
        vocals_energy = librosa.feature.rms(y=vocals_mono, frame_length=frame_length, hop_length=hop_length)[0]
        inst_energy = librosa.feature.rms(y=inst_mono, frame_length=frame_length, hop_length=hop_length)[0]
        
        # Create time-varying noise gate
        # Where instrumental energy is high relative to vocals, apply more suppression
        energy_ratio = inst_energy / (vocals_energy + 1e-10)
        noise_gate = 1.0 / (1.0 + energy_ratio * 0.3)
        
        # Apply noise gate with smoothing
        noise_gate_smooth = librosa.util.normalize(noise_gate)
        
        # Upsample gate to audio length
        gate_upsampled = np.interp(
            np.arange(len(vocals_mono)),
            np.arange(len(noise_gate_smooth)) * hop_length,
            noise_gate_smooth
        )
        
        # Apply gate
        vocals_gated = vocals_mono * gate_upsampled
        
        # Convert back to stereo if needed
        if vocals.shape[0] == 2:
            return np.stack([vocals_gated, vocals_gated])
        return vocals_gated

class KaraokeSeparator:
    """
    Main karaoke separator using Facebook's Demucs with vocal enhancement.
    """
    
    def __init__(self, 
                 output_dir: str = "./karaoke_output",
                 model_name: str = "htdemucs",
                 device: str = "auto",
                 quality: str = "high",
                 enhance_vocals: bool = True):
        """
        Initialize karaoke separator.
        
        Args:
            output_dir: Directory to save output files
            model_name: Demucs model ("htdemucs" recommended)
            device: Processing device ("auto", "cpu", "cuda", "mps")
            quality: Quality setting ("fast", "medium", "high")
            enhance_vocals: Whether to apply vocal enhancement post-processing
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.enhance_vocals = enhance_vocals
        
        # Set quality parameters
        quality_settings = {
            "fast": {"shifts": 1},
            "medium": {"shifts": 3}, 
            "high": {"shifts": 5}
        }
        shifts = quality_settings.get(quality, {"shifts": 1})["shifts"]
        
        # Initialize Demucs separator
        self.separator = DemucsKaraokeSeparator(
            model_name=model_name,
            device=device, 
            shifts=shifts
        )
        
        # Initialize vocal enhancer
        if self.enhance_vocals:
            self.vocal_enhancer = VocalEnhancer()
        
        self.audio_processor = AudioProcessor()
        
        enhance_msg = "with vocal enhancement" if enhance_vocals else "standard mode"
        logger.info(f"🎤 Karaoke Separator ready! Quality: {quality}, Model: {model_name}, {enhance_msg}")
        
    def process_song(self, input_file: str, song_name: Optional[str] = None) -> Dict[str, str]:
        """
        Process a song and create karaoke tracks with enhanced vocals.
        
        Args:
            input_file: Path to input audio file
            song_name: Optional name for output files
            
        Returns:
            Dictionary with paths to created files
        """
        logger.info(f"🎵 Processing: {input_file}")
        
        # Determine output filename
        if song_name is None:
            song_name = Path(input_file).stem
        
        # Load audio
        audio, sample_rate = self.audio_processor.load_audio(input_file)
        
        # Perform separation
        separated_sources = self.separator.separate(audio)
        
        # Create karaoke instrumental
        karaoke_track = self.separator.create_karaoke_track(separated_sources)
        
        # Enhance vocals if enabled
        vocals_final = separated_sources['vocals']
        if self.enhance_vocals and 'vocals' in separated_sources:
            logger.info("🎤 Applying vocal enhancement...")
            vocals_final = self.vocal_enhancer.enhance_vocals(
                separated_sources['vocals'],
                karaoke_track,
                audio
            )
        
        # Save all tracks
        output_files = {}
        
        # Save karaoke instrumental (main output)
        karaoke_path = self.output_dir / f"{song_name}_karaoke.wav"
        self.audio_processor.save_audio(karaoke_track, str(karaoke_path), sample_rate)
        output_files["karaoke"] = str(karaoke_path)
        
        # Save enhanced vocals (for lyrics generation)
        vocal_path = self.output_dir / f"{song_name}_vocals_clean.wav"
        self.audio_processor.save_audio(vocals_final, str(vocal_path), sample_rate)
        output_files["vocals"] = str(vocal_path)
        
        # Save raw vocals for comparison
        if self.enhance_vocals:
            vocal_raw_path = self.output_dir / f"{song_name}_vocals_raw.wav"
            self.audio_processor.save_audio(separated_sources['vocals'], str(vocal_raw_path), sample_rate)
            output_files["vocals_raw"] = str(vocal_raw_path)
        
        # Save individual stems (optional)
        for source_name, source_audio in separated_sources.items():
            if source_name not in ['vocals']:  # Don't duplicate vocals
                stem_path = self.output_dir / f"{song_name}_{source_name}.wav"
                self.audio_processor.save_audio(source_audio, str(stem_path), sample_rate)
                output_files[source_name] = str(stem_path)
        
        output_files.update({
            "original": input_file,
            "song_name": song_name,
            "instrumental": output_files["karaoke"]  # Alias
        })
        
        logger.info("🎉 Karaoke processing complete!")
        if self.enhance_vocals:
            logger.info("🎤 Enhanced vocals saved for clean lyrics extraction!")
        return output_files
    
    def batch_process(self, input_dir: str, file_extensions: list = [".mp3", ".wav", ".flac", ".m4a"]) -> list:
        """Process multiple files for karaoke."""
        input_path = Path(input_dir)
        results = []
        
        audio_files = []
        for ext in file_extensions:
            audio_files.extend(input_path.glob(f"*{ext}"))
        
        logger.info(f"📁 Found {len(audio_files)} audio files to process")
        
        for i, audio_file in enumerate(audio_files, 1):
            try:
                logger.info(f"[{i}/{len(audio_files)}] Processing: {audio_file.name}")
                result = self.process_song(str(audio_file))
                results.append(result)
                logger.info(f"✅ Completed: {audio_file.name}")
            except Exception as e:
                logger.error(f"❌ Failed {audio_file.name}: {e}")
                
        logger.info(f"🎉 Batch processing complete! {len(results)}/{len(audio_files)} successful")
        return results

# Quick helper functions
def quick_karaoke(input_file: str, output_dir: str = "./karaoke_output", quality: str = "medium", 
                 device: str = "cpu", enhance_vocals: bool = True):
    """
    Quick function to create karaoke track using Demucs with vocal enhancement.
    
    Args:
        input_file: Path to audio file
        output_dir: Output directory
        quality: "fast", "medium", or "high"
        device: "cpu", "cuda", or "auto" (defaults to CPU for stability)
        enhance_vocals: Whether to clean up the vocal track
    
    Example:
        quick_karaoke("song.mp3", enhance_vocals=True)
        # Creates song_karaoke.wav and song_vocals_clean.wav
    """
    separator = KaraokeSeparator(output_dir=output_dir, quality=quality, device=device, enhance_vocals=enhance_vocals)
    return separator.process_song(input_file)

def test_karaoke_quality(input_file: str):
    """Test karaoke separation quality with vocal enhancement."""
    print(f"🧪 Testing Demucs karaoke separation with vocal enhancement: {input_file}")
    
    result = quick_karaoke(input_file, quality="high", enhance_vocals=True)
    
    print(f"\n🎯 Results:")
    print(f"🎤 Karaoke track: {result['karaoke']}")
    print(f"🗣️ Clean vocals (for lyrics): {result['vocals']}")
    if 'vocals_raw' in result:
        print(f"🔍 Raw vocals (comparison): {result['vocals_raw']}")
    print(f"🥁 Drums: {result.get('drums', 'N/A')}")
    print(f"🎸 Bass: {result.get('bass', 'N/A')}")
    print(f"🎹 Other instruments: {result.get('other', 'N/A')}")
    
    print(f"\n✨ Compare the clean vs raw vocals:")
    print(f"   🎤 Clean: {result['vocals']} (should have much less background music)")
    if 'vocals_raw' in result:
        print(f"   🔍 Raw: {result['vocals_raw']} (original Demucs output)")
    return result

# Main execution
if __name__ == "__main__":
    def main():
        print("🎵 Professional Karaoke Separator (Powered by Demucs)")
        print("=" * 55)
        
        # Get input file
        input_file = input("📁 Enter path to your audio file: ").strip()
        
        if not input_file:
            print("\n💡 Usage examples:")
            print("   quick_karaoke('song.mp3')")
            print("   test_karaoke_quality('song.wav')")
            return
        
        if not os.path.exists(input_file):
            print(f"❌ File not found: {input_file}")
            return
        
        try:
            print(f"\n🚀 Processing with Demucs AI...")
            print(f"🧪 Testing Demucs karaoke separation with vocal enhancement: {input_file}")
            
            # Create separator and process
            separator = KaraokeSeparator(output_dir="./karaoke_output", quality="high", enhance_vocals=True)
            result = separator.process_song(input_file, "quality_test")
            
            print(f"\n🎯 Results:")
            print(f"🎤 Karaoke track: {result['karaoke']}")
            print(f"🗣️ Clean vocals (for lyrics): {result['vocals']}")
            if 'vocals_raw' in result:
                print(f"🔍 Raw vocals (comparison): {result['vocals_raw']}")
            print(f"🥁 Drums: {result.get('drums', 'N/A')}")
            print(f"🎸 Bass: {result.get('bass', 'N/A')}")
            print(f"🎹 Other instruments: {result.get('other', 'N/A')}")
            
            print(f"\n✨ Compare the clean vs raw vocals:")
            print(f"   🎤 Clean: {result['vocals']} (should have much less background music)")
            if 'vocals_raw' in result:
                print(f"   🔍 Raw: {result['vocals_raw']} (original Demucs output)")
            
            print(f"\n🎉 Success! Your karaoke track is ready!")
            print(f"📂 Check the output folder: {Path('./karaoke_output').absolute()}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print("\n🔧 Try installing dependencies:")
            print("   pip install demucs torch torchaudio scipy")
    
    main()