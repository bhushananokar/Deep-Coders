import io
import traceback
import streamlit as st

# Try to import gTTS, but handle if it's not available
try:
    from gtts import gTTS, gTTSError
except ImportError:
    # If gTTS is not installed, set it to None and print an error
    # The app will still run but TTS features will be disabled.
    print("ERROR: gTTS library not found. TTS features will be disabled. Install with: pip install gTTS")
    gTTS = None
    gTTSError = None

def generate_tts_audio(text: str):
    """Generates TTS audio using gTTS and returns BytesIO object."""
    if not gTTS or not text or not isinstance(text, str):
        # Silently return None if gTTS unavailable or text invalid
        # Errors will be handled where this function is called if needed
        return None
    try:
        # Limit text length to avoid overly long TTS requests/errors
        max_len = 1000
        if len(text) > max_len:
            text = text[:max_len] + "... (truncated for audio)"
            st.caption("(Audio truncated due to length)")

        tts = gTTS(text=text, lang='en', slow=False)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)  # Rewind the buffer
        return audio_fp
    except gTTSError as e:
        st.error(f"gTTS Error: {e}. Check internet connection or text content.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during TTS generation: {e}")
        traceback.print_exc()
        return None

def is_tts_available():
    """Check if TTS functionality is available"""
    return gTTS is not None