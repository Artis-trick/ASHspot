from pytube import YouTube
import os
from moviepy.editor import AudioFileClip

def youtube_to_mp3(video_url, output_folder="downloads"):
    try:
        # Create output folder if not exists
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Download video
        yt = YouTube(video_url)
        video_stream = yt.streams.filter(only_audio=True).first()
        output_path = video_stream.download(output_path=output_folder)

        # Convert to MP3
        mp3_path = os.path.join(output_folder, f"{yt.title}.mp3")
        audio_clip = AudioFileClip(output_path)
        audio_clip.write_audiofile(mp3_path)
        audio_clip.close()

        # Remove the original video file
        os.remove(output_path)

        print(f"MP3 saved at: {mp3_path}")

    except Exception as e:
        print(f"Error: {e}")

# Example usage
video_url = input("Enter the YouTube video URL: ")
youtube_to_mp3(video_url)
