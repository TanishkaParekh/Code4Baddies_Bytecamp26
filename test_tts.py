from gtts import gTTS

text = "This is a test of the prescription voice report."

tts = gTTS(text=text, lang="en")

tts.save("test_voice.mp3")

print("Voice file generated successfully!")