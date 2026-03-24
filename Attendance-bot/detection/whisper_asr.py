"""
Whisper Speech Recognizer (Optional / Fallback)
Uses OpenAI Whisper locally with NVIDIA GPU (CUDA) acceleration.
Only activates if captions are unavailable or unreliable.

Captures system audio via sounddevice and transcribes in real-time.
Requires: VB-Audio Virtual Cable or similar (for system audio capture).
"""

import asyncio
import threading
import queue
import numpy as np
from typing import Optional, Callable
from core.logger import setup_logger

logger = setup_logger("WhisperASR")


class WhisperRecognizer:
    def __init__(self, on_transcript: Optional[Callable] = None):
        self.on_transcript = on_transcript
        self.audio_queue: queue.Queue = queue.Queue()
        self.running = False
        self.model = None
        self._thread: Optional[threading.Thread] = None

    def _load_model(self):
        """Load Whisper model with GPU if available."""
        try:
            import whisper
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading Whisper model on {device.upper()}...")
            self.model = whisper.load_model("small", device=device)
            logger.info(f"Whisper loaded on {device.upper()}")
            return True
        except ImportError:
            logger.warning("Whisper not installed. pip install openai-whisper")
            return False
        except Exception as e:
            logger.error(f"Whisper load failed: {e}")
            return False

    def start(self):
        """Start audio capture and transcription in background thread."""
        if not self._load_model():
            return
        self.running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info("Whisper ASR started (background thread)")

    def stop(self):
        self.running = False
        logger.info("Whisper ASR stopped")

    def _capture_loop(self):
        """Capture 5-second audio chunks and transcribe."""
        try:
            import sounddevice as sd
            SAMPLE_RATE = 16000
            CHUNK_SECS = 5

            logger.info("Audio capture started (WASAPI loopback)")

            while self.running:
                audio = sd.rec(
                    int(CHUNK_SECS * SAMPLE_RATE),
                    samplerate=SAMPLE_RATE,
                    channels=1,
                    dtype="float32",
                )
                sd.wait()
                audio_np = audio.flatten()

                # Skip silent chunks
                if np.abs(audio_np).max() < 0.01:
                    continue

                result = self.model.transcribe(
                    audio_np,
                    language="ur",  # Urdu
                    fp16=True,
                    task="transcribe",
                )
                text = result.get("text", "").strip()

                if text and self.on_transcript:
                    logger.debug(f"[Whisper] Transcribed: {text}")
                    self.on_transcript(text)

        except Exception as e:
            logger.error(f"Audio capture error: {e}")
            logger.info("TIP: Install VB-Audio Virtual Cable to capture system audio")
            logger.info("     https://vb-audio.com/Cable/")


# ============================================================
# HOW TO USE (in MeetHandler):
#
# from detection.whisper_asr import WhisperRecognizer
#
# def on_transcript(text):
#     self.recent_captions.append(text)
#
# self.asr = WhisperRecognizer(on_transcript=on_transcript)
# self.asr.start()   # at join
# self.asr.stop()    # at leave
# ============================================================
