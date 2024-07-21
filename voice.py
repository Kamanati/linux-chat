import argparse
import nltk
from nltk.tokenize import sent_tokenize
from pydub import AudioSegment
import os,time
import sys,threading
import elevenlabs
from elevenlabs import save, play, generate

nltk.download('punkt')

"""
def split_text_into_chunks(text, char_limit=490):
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= char_limit:  # +1 for space/newline
            current_chunk += " " + sentence if current_chunk else sentence
        else:
            chunks.append(current_chunk)
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk)

    return chunks
"""

def split_text_into_chunks(text, char_limit=490):
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # Check if adding the current sentence would exceed the limit
        if len(current_chunk) + len(sentence) + 1 > char_limit:
            if current_chunk:
                chunks.append(current_chunk)
            # Start a new chunk with the current sentence
            current_chunk = sentence
        else:
            # Append the sentence to the current chunk
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence

    # Append the last chunk if it exists
    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def die(message):
    red = "\033[31m"
    reset = "\033[0m"
    print(f"[{red}WARNING{reset}] {message}")

def info(message):
    green = "\033[32m"
    r = "\033[0m"
    print(f"[{green}INFO{r}] {message}")

def printx(prompt, timeout):
    result = [None]
    prompt_updated = f"{prompt} (timeout in {timeout} seconds): "
    
    def get_input():
        result[0] = input(prompt_updated)
    
    def update_prompt():
        nonlocal prompt_updated
        for remaining in range(timeout, 0, -1):
            sys.stdout.write(f"\r{prompt} (timeout in {remaining} seconds): ")
            sys.stdout.flush()
            time.sleep(1)
        print("\nTimeout! No input received.")
    
    thread_input = threading.Thread(target=get_input)
    thread_input.daemon = True
    thread_input.start()
    
    thread_timer = threading.Thread(target=update_prompt)
    thread_timer.daemon = True
    thread_timer.start()
    
    thread_input.join(timeout)
    
    if thread_input.is_alive():
        return None
    return result[0]

# Usage example
def combine_audio_files(file_list, output_filename):
    combined = AudioSegment.empty()
    for file in file_list:
        audio = AudioSegment.from_file(file)
        combined += audio

    combined.export(output_filename, format=output_filename.split('.')[-1])
    info(f"Combined audio saved to: {output_filename}")

def main():
    parser = argparse.ArgumentParser(description="Generate and play or save audio from text.")
    parser.add_argument('text', nargs='?', type=str, help='The text to convert to audio.')
    parser.add_argument('-f', '--file', type=str, help='Path to a text file to convert to audio.')
    parser.add_argument('-p', '--play', action='store_true', help='Play the generated audio.')
    parser.add_argument('-s', '--save', type=str, help='Save the generated audio to a file (provide filename with .mp3 or .wav extension).')

    args = parser.parse_args()

    if not sys.stdin.isatty():
        # Read text from stdin (e.g., when piped from cat)
        info("Reading text from stdin...")
        text = sys.stdin.read()
    elif args.file:
        info(f"Reading text from file: {args.file}")
        try:
            with open(args.file, 'r') as file:
                text = file.read()
        except FileNotFoundError:
            die(f"File not found: {args.file}")
            return
    elif args.text:
        text = args.text
    else:
        die("Please provide either text, a file containing the text, or pipe the text through stdin.")
        return

    play_audio = args.play
    save_filename = args.save

    info("Splitting text into chunks...")
    chunks = split_text_into_chunks(text)
    info(f"Total chunks created: {len(chunks)}")

    temp_files = []

    for idx, chunk in enumerate(chunks):
        info(f"Generating audio for chunk {idx + 1} of {len(chunks)}...")
        try:
           audio_bytes = generate(text=chunk, voice="Freya", model="eleven_multilingual_v2")
        except Exception as e:
           die("Network Issue accured..")
           info(e)
        
        if play_audio:
            info(f"Playing audio for chunk {idx + 1} of {len(chunks)}...")
            play(audio_bytes)
        
        if save_filename:
            chunk_filename = f"{save_filename.rsplit('.', 1)[0]}_{idx + 1}.{save_filename.rsplit('.', 1)[1]}"
            info(f"Saving audio to file: {chunk_filename}")
            try:
               save(audio_bytes, chunk_filename)
               temp_files.append(chunk_filename)
            except Exception as e:
               die("Error accur3d")
               #printx("Press Enter to continue with in ",10)

    if save_filename:
        info("Combining all audio chunks into one file...")
        try:
            combine_audio_files(temp_files, save_filename)
            info("Deleting temporary chunk files...")
            for file in temp_files:
                os.remove(file)
            info("All temporary chunk files deleted successfully.")
        except Exception as e:
            die(f"An error occurred while combining audio files: {e}")

if __name__ == "__main__":
    main() 
