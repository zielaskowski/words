from bs4 import BeautifulSoup as bs
import requests
from .. import modules


lang='pl'
res = requests.get('https://pl.wiktionary.org/wiki/в')
#в последнее время
if lang == 'pl':
    h = 'h2'
    def right_hTag(tag):
        return tag.name == 'h2' and tag.find('span',class_='lang-code-ru')
else:
    h = 'h1'
    def right_hTag(tag):
        return tag.name == 'h1' and tag.find('span',id='Русский')

source = bs(res.content, 'lxml')
source = source.find('div',class_='mw-parser-output') # taking only interesting content, skipping, menus etc.
html = bs("<div></div>",'lxml') # here we store what interesting

hTag = source.find(right_hTag)
for tag in hTag.next_siblings:
    if tag.name == h:
        break
    if tag.name is not None:
        #  need to create new tag 'couse appending tag directly will destroy new_siblings generator
        new_tag = html.new_tag(tag.name)
        [new_tag.append(sub_tag) # tag can (and mostly have) few sub_tags so need to iterate
            for sub_tag in tag.contents if sub_tag.name is not None]
        html.div.append(new_tag)



znaczenia = bs("<div><h1>znaczenia</h1></div>",'lxml')

def rightDlTag(tag):
    return tag.name == 'dl' and tag.find('span',class_='fld-znaczenia')


dlTag = html.find(rightDlTag)
for sib in dlTag.next_siblings:
    if sib.find('span', class_=True): # all siblings down to next <dl> with class
        break
    new_tag = html.new_tag(sib.name)
    [new_tag.append(sub_tag) # tag can (and mostly have) few sub_tags so need to iterate
        for sub_tag in sib.contents if sub_tag.name is not None]
    znaczenia.div.append(new_tag)

# remove href links
for aTag in znaczenia.find_all('a'):
    aTag.unwrap()

print(znaczenia.prettify())

decli_pl = bs("<div><h1>odmiana</h1></div>",'lxml')

def rightDlTag(tag):
    return tag.name == 'dl' and tag.find('span',class_='fld-odmiana')

dlTag = html.find(rightDlTag)
for ddTag in dlTag.find_all('dd'):
    decli_pl.div.append(ddTag)

# remove href links
for aTag in decli_pl.find_all('a'):
    aTag.unwrap()

print(decli_pl.prettify())



exa = bs("<div><h1>przyklady</h1></div>",'lxml')

def rightDlTag(tag):
    return tag.name == 'dl' and tag.find('span',class_='fld-przyklady')

dlTag = html.find(rightDlTag)
for ddTag in dlTag.find_all('dd'):
    exa.div.append(ddTag)

# remove href links
for aTag in exa.find_all('a'):
    aTag.unwrap()

print(exa.prettify())


lang='ru'
res = requests.get('https://ru.wiktionary.org/wiki/надо')

if lang == 'pl':
    h = 'h2'
    def right_hTag(tag):
        return tag.name == 'h2' and tag.find('span',class_='lang-code-ru')
else:
    h = 'h1'
    def right_hTag(tag):
        return tag.name == 'h1' and tag.find('span',id='Русский')

source = bs(res.content, 'lxml')
source = source.find('div',class_='mw-parser-output') # taking only interesting content, skipping, menus etc.
html = bs("<div></div>",'lxml') # here we store what interesting

hTag = source.find(right_hTag)
for tag in hTag.next_siblings:
    if tag.name == h:
        break
    if tag.name is not None:
        #  need to create new tag 'couse appending tag directly will destroy new_siblings generator
        new_tag = html.new_tag(tag.name)
        [new_tag.append(sub_tag) # tag can (and mostly have) few sub_tags so need to iterate
            for sub_tag in tag.contents if sub_tag.name is not None]
        html.div.append(new_tag)



decli_ru = bs("<div><h1>odmiana</h1></div>",'lxml')

def tdWithClass(tag):
    return tag.name == 'td' and tag.has_attr('class')

# unfortunatelly we need to make negative selection
# reject table with list<li> or with class=*
tableTag = [tag for tag in html.find_all('table') 
                if not tag.find(tdWithClass) 
                    and not tag.find('li')]
if len(tableTag) > 0:
    decli_ru.div.append(tableTag[0])

# remove href links
for aTag in decli_ru.find_all('a'):
    aTag.unwrap()

# remove <sup> tag with content
for supTag in decli_ru.find_all('sup'):
    supTag.decompose()

print(decli_ru.prettify())

wiki = bs("<div><h2></h2></div>",'lxml')
wiki.h2.string = 'wrd[wrd_i]'
wiki.div.append(znaczenia)
wiki.div.append(decli_pl)
wiki.div.append(decli_ru)
wiki.div.append(exa)

print(wiki.content)