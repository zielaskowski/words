from bs4 import BeautifulSoup as bs
import requests
from modules import Wiki
from modules import FileSystem
import copy

#txt = 'привези его из школы год'.split()
#txt = list(txt)
txt = ['странный']

fs = FileSystem()
wiki = Wiki(fs.getTrans())
wiki.checkWiki(txt)
fa = wiki.readData(0)


for i in range(len(txt)):
    wiki.readData(i)
    print(wiki.data[i]['example_ru'])


print()