from bs4 import BeautifulSoup as bs
import requests
from modules import Wiki

txt = 'привези его из школы год'.split()
txt = list(txt)
txt = ['посетить']

wiki = Wiki()
wiki.checkWiki(txt)
for i in range(len(txt)):
    wiki.readData(i)
    print(wiki.data[i]['translation'])


print()