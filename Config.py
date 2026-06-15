"""Central configuration. Secrets come from environment variables, never hard-coded."""
import os

# --- Azure Speech ---
AZURE_SPEECH_KEY = os.environ.get("AZURE_SPEECH_KEY", "47e0d89105c1425582baf32853502a55")
AZURE_SPEECH_REGION = os.environ.get("AZURE_SPEECH_REGION", "japaneast")
AZURE_VOICE = os.environ.get("AZURE_VOICE", "ja-JP-NanamiNeural")
SPEECH_LANG = "ja-JP"

# MP3 output format used by the Azure SDK
AZURE_AUDIO_FORMAT = "Audio16Khz128KBitRateMonoMp3"

# --- Fixed List persistence (SQLite file) ---
FIXED_LIST_EXCEL = os.environ.get("FIXED_LIST_EXCEL", r"D:\Phd\Project-Code\DATA\Language\dicJP6_originalUpdated.xlsx")