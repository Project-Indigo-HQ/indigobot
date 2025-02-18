import chainlit as cl
import os
import speech_recognition as sr
from gtts import gTTS
from io import BytesIO
import pygame
import tempfile
from langchain.schema import AIMessage, HumanMessage
from indigobot.config import llm, vectorstore
from indigobot.context import call_model

# Initialize pygame for audio playback
pygame.mixer.init()


def text_to_speech(text):
    """Converts text to speech and plays the audio."""
    
    # Generate speech audio
    tts = gTTS(text)
    
    # Create a temporary file for cross-platform compatibility
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        temp_audio_path = temp_audio.name
        tts.save(temp_audio_path)

    # Play the audio using pygame
    pygame.mixer.music.load(temp_audio_path)
    pygame.mixer.music.play()

    # Wait until the audio finishes playing
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    # Cleanup: Remove the temporary file after playback
    os.remove(temp_audio_path)

    return temp_audio_path  # Returning path just in case it's needed


# Function to convert speech to text
def speech_to_text():
    """Capture voice input and return the recognized text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for input...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)  # 5s timeout
            text = recognizer.recognize_google(audio)
            print(f"Recognized: {text}")
            return text
        except sr.UnknownValueError:
            print("Could not understand audio.")
        except sr.RequestError:
            print("Error with speech recognition service.")
    return ""


@cl.on_message
async def on_message(message: cl.Message):
    """Handles user messages in the Chainlit chat."""
    
    # Handle STT
    if message.content.strip().lower() == "voice":
        message.content = speech_to_text() or "Sorry, I didn't catch that."

    # Construct state for chatbot
    state = {
        "input": message.content,
        "chat_history": [],
        "context": "",
        "answer": "",
    }
    
    # Get chatbot response
    response = call_model(state)
    bot_reply = response["answer"]
    
    # Send response in chat
    await cl.Message(bot_reply).send()
    
    # Convert bot response to speech
    text_to_speech(bot_reply)


if __name__ == "__main__":
    cl.run()
