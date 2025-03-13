"""This module leverages Chainlit to create a web UI for the chatbot."""

import audioop
import io
import os
import tempfile
import wave

import chainlit as cl
import numpy as np
from gtts import gTTS
from openai import AsyncOpenAI

from indigobot.utils.etl.custom_loader import start_loader
from indigobot.__main__ import main as indybot

openai_client = AsyncOpenAI()

# Define a threshold for detecting silence and a timeout for ending a turn
# Adjust based on your audio level (e.g., lower for quieter audio)
SILENCE_THRESHOLD = 3500
SILENCE_TIMEOUT = 1300.0  # Seconds of silence to consider the turn finished


@cl.on_chat_start
async def start():
    start_loader()
    """Examples for setting/getting sessions"""
    # app_user = cl.user_session.get("user")
    # print(f"hello id: {cl.user_session.get("id")} user: {app_user} identifier: {app_user.identifier}")
    # cl.user_session.set("message_history", [])

    """Examples for creating/updating settings"""


#     settings = await cl.ChatSettings(
#         [
#             Select(
#                 id="Model",
#                 label="OpenAI - Model",
#                 values=["gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4", "gpt-4-32k"],
#                 initial_index=0,
#             ),
#             Switch(id="Streaming", label="OpenAI - Stream Tokens", initial=True),
#             Slider(
#                 id="Temperature",
#                 label="OpenAI - Temperature",
#                 initial=1,
#                 min=0,
#                 max=2,
#                 step=0.1,
#             ),
#         ]
#     ).send()


# @cl.on_settings_update
# async def setup_agent(settings):
#     print("on_settings_update", settings)

"""Example of user login implementation"""
# @cl.password_auth_callback
# def auth_callback(username: str, password: str):
#     # Fetch the user matching username from your database
#     # and compare the hashed password with the value stored in the database
#     if (username, password) == ("admin", "admin"):
#         return cl.User(
#             identifier="admin", metadata={"role": "admin", "provider": "credentials"}
#         )
#     else:
#         return None


@cl.on_audio_start
async def on_audio_start():
    cl.user_session.set("silent_duration_ms", 0)
    cl.user_session.set("is_speaking", False)
    cl.user_session.set("audio_chunks", [])
    return True


# Receives audio messages
@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    audio_chunks = cl.user_session.get("audio_chunks")

    if audio_chunks is not None:
        audio_chunk = np.frombuffer(chunk.data, dtype=np.int16)
        audio_chunks.append(audio_chunk)

    # If this is the first chunk, initialize timers and state
    if chunk.isStart:
        cl.user_session.set("last_elapsed_time", chunk.elapsedTime)
        cl.user_session.set("is_speaking", True)
        return

    audio_chunks = cl.user_session.get("audio_chunks")
    last_elapsed_time = cl.user_session.get("last_elapsed_time")
    silent_duration_ms = cl.user_session.get("silent_duration_ms")
    is_speaking = cl.user_session.get("is_speaking")

    # Calculate the time difference between this chunk and the previous one
    time_diff_ms = chunk.elapsedTime - last_elapsed_time
    cl.user_session.set("last_elapsed_time", chunk.elapsedTime)

    # Compute the RMS (root mean square) energy of the audio chunk
    # Assumes 16-bit audio (2 bytes per sample)
    audio_energy = audioop.rms(chunk.data, 2)

    if audio_energy < SILENCE_THRESHOLD:
        # Audio is considered silent
        silent_duration_ms += time_diff_ms
        cl.user_session.set("silent_duration_ms", silent_duration_ms)
        if silent_duration_ms >= SILENCE_TIMEOUT and is_speaking:
            cl.user_session.set("is_speaking", False)
            await process_audio()
    else:
        # Audio is not silent, reset silence timer and mark as speaking
        cl.user_session.set("silent_duration_ms", 0)
        if not is_speaking:
            cl.user_session.set("is_speaking", True)


async def process_audio():
    # Get the audio buffer from the session
    if audio_chunks := cl.user_session.get("audio_chunks"):
        # Concatenate all chunks
        concatenated = np.concatenate(list(audio_chunks))

        # Create an in-memory binary stream
        wav_buffer = io.BytesIO()

        # Create WAV file with proper parameters
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)  # mono
            wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
            wav_file.setframerate(24000)  # sample rate (24kHz PCM)
            wav_file.writeframes(concatenated.tobytes())

        # Reset buffer position
        wav_buffer.seek(0)

        cl.user_session.set("audio_chunks", [])

    audio_buffer = wav_buffer.getvalue()
    whisper_input = ("audio.wav", audio_buffer, "audio/wav")

    transcription = await speech_to_text(whisper_input)
    await cl.Message(
        author="You",
        type="user_message",
        content=transcription,
    ).send()

    response = indybot(transcription)

    actions = [
        cl.Action(
            name="text-to-speech",
            payload={"value": response},
            label="play audio",
        )
    ]
    await cl.Message(content=f"{response}", actions=actions).send()


@cl.step(type="tool")
async def speech_to_text(audio_file):
    response = await openai_client.audio.transcriptions.create(
        model="whisper-1", file=audio_file
    )
    return response.text


@cl.action_callback("text-to-speech")
async def on_action(action):
    text = action.payload["value"]
    # Generate speech audio
    tts = gTTS(text)

    # Create a temporary file for cross-platform compatibility
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio_path = temp_audio.name
        tts.save(temp_audio_path)

    elements = [
        cl.Audio(
            name="audio response",
            path=temp_audio_path,
            display="inline",
            auto_play=True,
        ),
    ]
    await cl.Message(content="", elements=elements).send()

    os.remove(temp_audio_path)

    await action.remove()


# Receives regular text messages
@cl.on_message
async def main(message: cl.Message):
    """Handle user input and send response from chatbot."""

    indybot_res = indybot(message.content)

    actions = [
        cl.Action(
            name="text-to-speech",
            payload={"value": indybot_res},
            label="play audio",
        )
    ]
    await cl.Message(content=f"{indybot_res}", actions=actions).send()
