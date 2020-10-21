from gtts import gTTS
import playsound

file = 'C:\\Users\\212348332\\Box Sync\\docs\\!!tools\\python\\words\\opt\\word.mp3'



word_sound = gTTS('профе́ссия', lang='ru')
word_sound.save(file)
playsound.playsound(file)

print()
