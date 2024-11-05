import os
import subprocess

def preprocess_audio_file(file_path: str) -> str:
    """
    Converts the input audio or video file to a WAV format with a 16kHz sample rate and mono channel.
    If the input is a video file, the function extracts audio using FFmpeg.

    Args:
        file_path (str): Path to the input audio or video file.

    Returns:
        str: The path to the preprocessed WAV file.
    """
    output_wav_file = f"{os.path.splitext(file_path)[0]}_converted.wav"

    # Use FFmpeg to convert or extract audio, ensuring 16kHz sample rate and mono channel
    cmd = f'ffmpeg -y -i "{file_path}" -ar 16000 -ac 1 "{output_wav_file}"'
    subprocess.run(cmd, shell=True, check=True)

    return output_wav_file