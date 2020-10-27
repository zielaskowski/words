from bs4 import BeautifulSoup as bs
import requests
from words.modules import Wiki
from words.modules import FileSystem

txt = 'привези его из школы год'.split()
txt = list(txt)
txt = ['странный']

fs = FileSystem()
wiki = Wiki(fs.getTrans())
wiki.checkWiki(txt)
for i in range(len(txt)):
    wiki.readData(i)
    print(wiki.data[i]['declination_ru'])


print()