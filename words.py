from gui import GUIWords, QApplication, GUIWordsCtr
import sys



app = QApplication([])
view = GUIWords()
view.show()
GUIWordsCtr(view)
sys.exit(app.exec())




# dic = Dictionary()
# file_path = '/home/mi/Dropbox/dokumenty/ruski/slowka.txt'
# file_db = '/home/mi/Dropbox/prog/python/words/dic.s3db'
#
# dic.open_sql_db(file_db)
# with open(file_path, 'r') as file:
#     slowka = file.readlines()
# dic.add(slowka)
# print(dic.err)
# dic.write_sql_db(file_db)
#
#
# while True:
#     com = input("(N)ext (R)epeat (P)revious r(A)nd e(X)it\n?>").lower()
#     if com == 'a':
#         row = dic.print()
#     if com == 'n':
#         row = dic.next()
#     if com == 'p':
#         row = dic.previous()
#     if com == 'r':
#         row = dic.print(dic.history[dic.history_index])
#     if com == 'x':
#         break
#     print(row.pl + ' <==> ' + row.ru)
#     print(dic.history)
#     print(dic.history_index)
#     word_sound = gTTS(text=row.ru, lang='ru')
#     word_sound.save("word.mp3")
#     os.system("mpg123 word.mp3 &>/dev/null")
#     dic.score()
# dic.write_sql_db(file_db)