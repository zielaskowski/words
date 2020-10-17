import os
import random
import copy
import re  # include sub method to use regex
import sqlite3
import sys
import pandas as pd
import json
import treetaggerwrapper
from bs4 import BeautifulSoup as bs
import requests


class Dictionary:
    """store pairs of words as pandas.DataFrame
    
    can add or print a pair of words
    parse input and check if correct
    
    When asked for word from dic, parse it through tagger and store gramma and lemma
    can be accessed through self.tager.formatAll()
    """

    def __init__(self, tagDesc_file, tagTrans_file):
        # main DB to store dictionary
        self.db = pd.DataFrame([['','',0,0]], columns=['ru', 'pl', 'try_n', 'fail_n'])
        # temp DB to store import date before commit
        self.db_temp = pd.DataFrame(columns=['ru', 'pl'])
        self.err = ''
        self.history = [0]
        self.history_index = 0
        # need to provide location for tags description file and translation of the tags
        self.tager = TTager(tagDesc_file, tagTrans_file)
        # read data from wiki
        self.wiki = Wiki()

    def importTXT(self, words):
        """allowed input formats:

        "пожаловать		Witamy", str,  words separated with white characters

        or list of strings as above: result of file.readlines()
        """
        self.err = ''
        self.db_temp = self.db_temp.iloc[0:0] # reset data frame
        if type(words) == list:
            for w in words:
                if type(w) == str:
                    self.__add_str__(w)
                else:
                    self.err += f'<p>IMPORT: Can process only strings, instead found {type(w)}</p>'
        elif type(words) == str:
            self.__add_str__(words)
        else:
            self.err += f'Not allowed type {type(words)}\n'
        self.db_temp.reset_index(inplace=True, drop=True)
        # remove rows already existing in self.db
        db_merge = pd.merge(self.db, self.db_temp, left_on = ['ru', 'pl'], right_on=['ru', 'pl'], how='right', indicator=True)
        rows_keep = db_merge['_merge'] == 'right_only'
        rows_drop = [not i for i in rows_keep]
        db_drop = db_merge[rows_drop]
        len_raw = len(self.db_temp)
        self.db_temp = db_merge[rows_keep]
        self.db_temp = self.db_temp.iloc[:,0:2]
        len_fin = len(self.db_temp)
        dup_no = len_raw - len_fin
        err = ''
        if dup_no:  # If there are duplicates...
            # remove errors for duplicated words
            # it's possible for "not-sure" translation infos
            # check if error belongs to droped word
            for line in self.err.split('</p>'):
                if not True in [line.find(w) > -1 for w in db_drop['ru']]:
                    err += line
            self.err = err
           
            self.err += f'<p>Number of duplicates in active DB: {len_raw - len_fin}</p>'
        if not self.err:
            self.err = '<p>No errors</p>'
        return self.db_temp

    def commit(self):
        self.db = self.db.append(self.db_temp, ignore_index=True)
        self.db.drop_duplicates(inplace=True)
        # remove empty rows: one is created at very begining
        self.db = self.db[self.db.ru != '']
        self.db = self.db.fillna(0)
        self.db.reset_index(inplace=True, drop=True)
        # if adding single line, so set history and history_index to newly added line
        if len(self.db_temp) == 1:
            self.history.append(len(self.db) - 1)
            self.history_index = len(self.history) - 1

    def __add_str__(self, words):
        line = self.__parse_str__(words)
        if line:
            # line += [0, 0]
            line_s = pd.Series(line, index=self.db_temp.columns)
            self.db_temp = self.db_temp.append(line_s, ignore_index=True)
            self.db_temp.drop_duplicates(inplace=True)

    def __parse_str__(self, line):
        '''split ru word from pl word
        it's allowed to have only ru word (without translation)
        division between ru and pl is any white char EXCEPT single space (more than one space will divide also)
        single space may mean two tnhnigs:
        - single ru word and translation
        - two word ru without translation
        will use tagger to check if second word is ru
        '''
        line = line.strip()  # remove space at beginning and at the end
        if re.findall(r'(?<!\s) (?!\s)',  line) and len(line.split()) == 2:  # if only one space and no other whitespace around
            # second word can be pl or ru
            words = line.split() 
            self.tager.tag(words[1]) # hopefully tagger will recognize ru word
            gram = [gram for gram in self.tager._gramma[0].iloc[1,:] if gram is not 'none']
            if not gram: # tager returned none
                self.wiki.checkWiki([words[1]], lang=['ru']) # double check with wiki
                if self.wiki.wrd[0] != '': # jednak cos znalezlismy
                    return [line,''] # wiki found ru word so no translation
                else:
                    self.err += f"<p>Not sure if correct: ru:<b>{words[0]}</b>  pl:<b>{words[1]}</b> YES?</p>"
                    return words # tager did not recognize: assume pl
            else:
                return [line,''] # tager found ru word so no translation
        line = re.sub(r'(?<!\s) (?!\s)', '_', line)  # single spaces replace with '_' to keep two-words combos together
        words = line.split()  # all other whitespaces separate the translation
        # if missing pl translation
        if len(words) == 1:
            words = [w.replace('_', ' ') for w in words]  # don't need underscore anymore
            words.append('')
            self.err += f"<p>Missing translation for <b>{words}</b></p>"
        if len(words) != 2:
            if words:  # don't need to report empt lines []
                self.err += f'<p>More or less than two words: <b>{words}</b></p>'
            return ''
        words = [w.replace('_', ' ') for w in words]  # don't need underscore anymore
        return words

    def print(self, line_no=-1) -> pd.Series:
        """return row from DB

        Requires row number. If empty, will return random row.
        To return current row use self.history and self.history_index
        """
        if line_no == -1:  # return rand line
            random.seed()
            mid_hits = max(self.db.try_n) // 2  # rand only from numbers with try count less than half of max
            if min(self.db.try_n) > mid_hits:
                mid_hits = min(self.db.try_n)
            # count all rows with try_n < mid_hits
            db_low = self.db[self.db.try_n <= mid_hits]
            line_no = random.randint(0, len(db_low) - 1)
            # need to find row no in full DB (db_low keeps original index so series.name solve the issue)
            line_no = db_low.iloc[line_no].name
            self.history.append(line_no)
            self.history_index = len(self.history) - 1
            row = self.db.iloc[line_no]
        else:  # return selected line
            row = self.db.iloc[line_no]
        #  tag the word (or words) providing grammar and lemma
        self.tager.tag(row.ru)
        #  check if wiki page exist for the row
        self.wiki.checkWiki(self.tager._lemma)


        return row

    def score(self, fail_no=0):
        self.db.iloc[self.history[self.history_index], 2] += 1
        self.db.iloc[self.history[self.history_index], 3] += fail_no

    def write_sql_db(self, file):
        if os.path.isfile(file):
            os.remove(file)
        db_file = sqlite3.connect(file)
        self.db.to_sql('dic', db_file, if_exists='replace', index=False)

    def open_sql_db(self, file):
        try:
            db_file = sqlite3.connect(file)
            self.db = pd.read_sql_query("SELECT * FROM dic", db_file)
            #  TODO: check if proper file and properly opened
            self.history = [0]
            self.history_index = 0
            return True
        except:
            return None

    def previous(self, n=1):
        self.history_index -= n
        if self.history_index < 0:
            self.history_index = 0
        return self.print(self.history[self.history_index])

    def next(self, n=1):
        deep = len(self.history) - self.history_index - 1  # how deep we are in history?
        if deep >= n:  # we are in past and we stay in past
            self.history_index += n
        elif deep == 0:  # we are in present
            self.history_index += 1
            self.history.append(self.history[-1] + n)
        else:  # we are not deep enough in past
            n -= deep
            self.history_index += 1
            self.history.append(self.history[-1] + n)
        return self.print(self.history[self.history_index])

    def drop(self, row_no):
        self.db.drop(self.db.index[row_no], inplace=True)
        self.db.reset_index(inplace=True, drop=True)
        # remove dropped line from history
        self.history = [i if i < row_no else i - 1 for i in self.history if i !=row_no]
        if not self.history:
            self.history = [0]
        if self.history_index > len(self.history) - 1:
            self.history_index = len(self.history) - 1



class FileSystem:
    """Handles all file system stuff

    Define file path and names. For each type stores as list of path, name and extensions:\n
    -imported TXT file:          self._fileTXT, access through self.getIMP and self.setIMP\n
    -temporary words.mp3 file:   self._fileMP3, access through self.getMP3\n
    -DB file:                    self._fileDB, access through self.getDB and self.setDB\n
    -aplication location:        self._fileAPP, access through self.getAPP\n
    -configuration file:         self._fileCONF, access to options through self.getOpt and self.writeOpt\n
    -tagset description for tagger
    -tagset translation to pl

    Handles expected type of file: SQlite3, TXT used as parameter for QtFileDialog
    """

    _PS = os.path.sep  # / for linux; \\ for win
    _PATH = 0  # location of path in self._fileXXX list
    _NAME = 1  # location of name in self._fileXXX list
    _EXT = 2  # location of extension in self._fileXXX list
    def __init__(self):
        self._fileIMP = []
        self._fileDB = []
        self._fileAPP = []
        self._fileMP3 = ['opt', 'word', '.mp3']  # name is constant, path will be taken from self._fileAPP
        self._fileCONF = ['opt', 'conf', '.txt']  # Configuration file. name is constant
        self._fileTags = ['opt', 'RU_tagset', '.txt'] #  Tags description for tagger
        self._fileTagsTrans = ['./opt/', 'RU_tagset_trans', '.txt'] # Tags translation to pl
        self.option = ["LastDB", "style"]
        self.typeIMP = ['text', '.txt']
        self.typeDB = ['SQlite3', '.s3db']
        
        self.setAPP()
        self._fileMP3[self._PATH] = self._fileAPP[self._PATH] + self._fileMP3[self._PATH] + self._PS
        self._fileCONF[self._PATH] = self._fileAPP[self._PATH] + self._fileCONF[self._PATH] + self._PS
        self._fileTags[self._PATH] = self._fileAPP[self._PATH] + self._fileTags[self._PATH] + self._PS
        self._fileTagsTrans[self._PATH] = self._fileAPP[self._PATH] + self._fileTagsTrans[self._PATH] + self._PS
        self._touchCONF()
    
    def getTags(self, path_only=False, file_only=False):
        """Returns file path (inculding filename) to Tags description file

        Tagger return symbolic description, file translate symbols to meaningfull description
        TODO: in case file is missing download from gitHUB
        """

        if path_only:
            return self._fileTags[self._PATH]
        elif file_only:
            return self._fileTags[self._NAME] + self._fileTags[self._EXT]
        else:  #all: path+name+ext
            return self._fileTags[self._PATH] + self._fileTags[self._NAME] + self._fileTags[self._EXT]

    def getTagsTrans(self, path_only=False, file_only=False):
        """Returns file path (inculding filename) to Tags translation file

        Tags description are in EN, file contain translation to PL
        TODO: in case file is missing download from gitHUB
        """

        if path_only:
            return self._fileTagsTrans[self._PATH]
        elif file_only:
            return self._fileTagsTrans[self._NAME] + self._fileTagsTrans[self._EXT]
        else:  #all: path+name+ext
            return self._fileTagsTrans[self._PATH] + self._fileTagsTrans[self._NAME] + self._fileTagsTrans[self._EXT]

    def getMP3(self, path_only=False, file_only=False):
        """Returns file path (inculding filename) to mp3 file

        mp3 file is used to store temporary the prononcuation of the word
        recived from Google (gTTS). If appropraite option is given, can return only
        path or only filename
        """

        if path_only:
            return self._fileMP3[self._PATH]
        elif file_only:
            return self._fileMP3[self._NAME] + self._fileMP3[self._EXT]
        else:  #all: path+name+ext
            return self._fileMP3[self._PATH] + self._fileMP3[self._NAME] + self._fileMP3[self._EXT]

    def setIMP(self, path):
        self._fileIMP = self._split_path(path[0])

    def getIMP(self, path_only=False, file_only=False, ext_type=False):
        if ext_type:  # 'Text (*.txt)'
            return self.typeIMP[0] + ' (*' + self.typeIMP[1] + ' *.*)'
        if not self._fileIMP:
            return []
        if path_only:
            return self._fileIMP[self._PATH]
        elif file_only:
            return self._fileIMP[self._NAME] + self._fileIMP[self._EXT]
        else:  #all: path+name+ext
            return self._fileIMP[self._PATH] + self._fileIMP[self._NAME] + self._fileIMP[self._EXT]

    def setDB(self, path: list):
        """set path and filename for DB.
        """
        # override file extension. No other than s3db can be opened
        self._fileDB = self._split_path(path)
        self._fileDB[self._EXT] = self.typeDB[1]

    def getDB(self, path_only=False, file_only=False, ext_type=False):
        """input typical for QtFileDialog: ('/..../dic_empty.txt', 'SQlite3 (*.s3db)')
        """
        if ext_type:  # 'SQlite (*.s3db)'
            return self.typeDB[0] + ' (*' + self.typeDB[1] + ')'
        if not self._fileDB: 
            return []
        if path_only:
            return self._fileDB[self._PATH]
        elif file_only:
            return self._fileDB[self._NAME] + self._fileDB[self._EXT]
        else:  #all: path+name+ext
            return self._fileDB[self._PATH] + self._fileDB[self._NAME] + self._fileDB[self._EXT]

    def setAPP(self):
        if getattr(sys, 'frozen', False):  # exe file
            file = os.path.realpath(sys.executable)
        else:
            try:
                file = os.path.realpath(__file__)  # debug in IDE
            except NameError:
                file = os.getcwd()  # command line >python3 app.py
        self._fileAPP = self._split_path(file)

    def getCONF(self, path_only=False, file_only=False, ext_type=False):
        """Returns file path (inculding filename) to config file.

        config file is used to store app configuration (at this moment only
        name of DB file when exited last time). If appropraite option is given,
        can return only path or only filename
        """
        if path_only:
            return self._fileCONF[self._PATH]
        elif file_only:
            return self._fileCONF[self._NAME] + self._fileCONF[self._EXT]
        else: #all: path+name+ext
            return self._fileCONF[self._PATH] + self._fileCONF[self._NAME] + self._fileCONF[self._EXT]

    def writeOpt(self, op, val):
        """write new value for option
        allowed options:
        LastDB - last DB when app was closed
        style - nothing yet
        """
        if op not in self.option:
            return 'nie ma takiej opcji'
        with open(self.getCONF(), 'r') as file:
            conf = json.load(file)
        conf[op] = val
        with open(self.getCONF(), 'w') as file:
            json.dump(conf, file)

    def getOpt(self,op):
        """Get value or option
        allowed options:
        LastDB - last DB when app was closed
        style - nothing yet
        """
        with open(self.getCONF(),'r') as file:
            conf = json.load(file)
        return conf[op]

    def _touchCONF(self):
        """Make sure the config file exists and has proper content
        Removes wrong entries, add entries if missing
        """
        ref_conf = {}
        with open(self.getCONF(), 'r+') as file: #  will create file if not exist
            try:
                conf = json.load(file)
            except:
                conf = {'new conf tbc': ''} #  empty file
        for op in self.option: # check here for known options
            if op not in conf:
                ref_conf[op] = ''
            else:
                ref_conf[op] = conf[op]
                conf.pop(op)
        if len(conf) > 0: # unknown options
            self._repairCONF(ref_conf)

    def _repairCONF(self, conf: dict):
        """create new fresh conf file
        """
        with open(self.getCONF(), 'w') as file:
            json.dump(conf, file)

    def _split_path(self, file):
        """split the string by path separator. Last list item is name.
        What is left is the path. Than name is split by dot, giving extension
        """

        path = ''
        file = file.split(self._PS)  # path separator is system specific (/ for linux, \ for win)
        name = file.pop()
        path = self.list2str(file, self._PS)
        name = name.split('.')
        if len(name) > 1:
            ext = name.pop()
        else:
            ext = ''
        name = self.list2str(name, '.')
        # dot between name and extension move to extension
        name = name[0:-1]
        ext = '.' + ext
        return [path, name, ext]

    def list2str(self, li, sep=''):
        str = ''
        for i in li:
            str += i + sep
        return str



class TTager:
    """Return grammar description of the word with lemma.

    Using treetagger wraper, to work you need treetagger executable with parameter files:
    https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/
    1. Download the tagger package for your system (PC-Linux, Mac OS-X, ARM64, ARMHF, ARM-Android, PPC64le-Linux).
    https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.3.tar.gz
    2. Download the installation script install-tagger.sh
    https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/install-tagger.sh
    3. Download the parameter files for the languages you want to process.
    RU_params: https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/russian.par.gz
    RU_tags: https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/russian.par.gz
    Open a terminal window and run the installation script in the directory where you have downloaded the files:
    sh install-tagger.sh

    how to make sure treetagger is installed (or install if needed) in
    executable version of this app is an open point...

    Treetagger will do no more than just simply report tags for 
    word already tagged (reasonably enough?)
    Alternative can be CSTlemma learned on treetagger:
    http://corpus.leeds.ac.uk/mocky/
    ,or NLTK taggers learned on RU corpus. If corpus is avilable i'm not sure...
    http://prac.im.pwr.wroc.pl/~szwabin/assets/unst/lec/8.pdf
    page 17
    or maybe RDRPOSTtagger, looks very promising
    http://rdrpostagger.sourceforge.net/
    """
    def __init__(self, tagDesc_file, tagTrans_file):
        #  we can have more then one word, we have list for each word
        self._gramma = [] #  gramatical description of the word
        self._lemma = [] #  lemma form of the word
        self.wrd = [] # word itself
        self.wrd_len = 0 # number of words
        # initialize tagger
        self.tag_eng = treetaggerwrapper.TreeTagger(TAGLANG='ru')
        #  get tags description and translation
        self.tagDesc = self._readTags(tagDesc_file)
        self.tagTrans = self._readTagsTrans(tagTrans_file)

    def _readTags(self, file):
        # read tagset file (description of tags)
        tagset = pd.read_csv(file, sep='\t')
        # from magic reason, header is repeated (drop_duplicates will not work,
        # as first header is already ... header)
        tagset = tagset.loc[tagset.MSD != 'MSD']
        # some values are '-' so convert to NaN 
        tagset.replace('-', pd.NA, inplace=True)
        return(tagset)

    def _readTagsTrans(self, file):    
        # read tagset translation
        tagset_trans = pd.read_csv(file, sep='\t', names=["ru","pl","del"])
        tagset_trans = tagset_trans.iloc[:,0:2] # in case some tabs on end of the line
        return(tagset_trans)

    def tag(self, wrd):
        #  avoid repetition
        if wrd.split(' ') == self.wrd:
            return
        # clear data from previous translation
        self._gramma = []
        self._lemma = []
        # store word for later, so we know where the gramma and lemma belongs
        self.wrd = wrd.split(' ')
        self.wrd_len = len(self.wrd)
        # If you have an external chunker, you can call the tagger with
        # option ``tagonly`` set to True, you should then provide a simple
        # string with one token by line (or list of strings with one token
        # by item).
        for wrd_i in range(self.wrd_len):
            tag = self.tag_eng.tag_text(self.wrd[wrd_i], tagonly=True)
            # may be empty for empty word
            if not tag:
                tag = ['\t\t']
            tag = tag[0].split('\t') # also for single word, tagger return the result in one element list
            self._gramma.append(self._grammaDesc(tag[1]))
            self._lemma.append(tag[2])
    
    def _grammaDesc(self, gramma_code):
        # find tag identifier in tags description
        gramma_trans = self.tagDesc[self.tagDesc.MSD == gramma_code]
        # drop all NaN
        gramma_trans = gramma_trans.dropna(axis=1) #, inplace= True)
        # drop first column, being the MSD which is short identifier
        gramma_trans = gramma_trans.iloc[:,1:]
        # move col names to first row, so translation work well also for headers
        if gramma_trans.empty:
            gramma_trans = pd.DataFrame(["CATEGORY","none"],columns=["CATEGORY"])
        else:
            gramma_trans = pd.DataFrame([gramma_trans.columns,
                                       gramma_trans.iloc[0,:].to_list()],
                                       columns = gramma_trans.columns)
        # translate to PL
        gramma_trans.replace(to_replace=self.tagTrans.ru.to_list(),
                            value=self.tagTrans.pl.to_list(),
                            inplace=True)
        return gramma_trans
    
    def formatAll(self, wrd_i):
        gram_desc_str=""
        # change df to str and nice format
        gram_desc_str += '<p align="center"><span style=" font-weight:600;">' + self.wrd[wrd_i].upper() + '</span></p>'
        for col in self._gramma[wrd_i].columns:
            gram_desc_str += '<p>' + self._gramma[wrd_i].loc[0,col].upper().strip() + ": " + self._gramma[wrd_i].loc[1,col].strip() + "</p>"
        gram_desc_str += "<p>-----------</p>"
        gram_desc_str += "<p>" + "LEMMA: " + self._lemma[wrd_i] + "</p>"
        return(gram_desc_str)



class Wiki:
    ''' extracts interesting info from wiki dictionary
        need to handle accent in words (need to be removed)
    '''
    def __init__(self):
        self._url = {'ru': "https://ru.wiktionary.org/wiki/",
                     'pl': "https://pl.wiktionary.org/wiki/"}
        self._html_it = {'pl': '',
                      'ru': ''} #  HTML content will be here (bs objects)
        self._html = [] #  _html{} for each word put to list
        self.data_it = {'translation': '',
                     'declination_pl': '',
                     'example': '',
                     'declination_ru': ''} # extracted data from HTML will be here (raw HTML) 
        self.data = [] #  data{} for each word put to list
        self.wrd = []
        
    def readData(self, wrd_i):
        '''read data from wiki only if wrd exist.
        self.checkWiki must be run first
        '''
        if not self.wrd[wrd_i]:
            return '<p align="center"><span style=" font-weight:600;">no data</span></p>'
        if self._html[wrd_i]['pl'] or self._html[wrd_i]['ru']:
            return self.formatAll(wrd_i)
        parse_check = 0
        for lang in self._url:
            wiki_resp = requests.get(self._url[lang] + self.wrd[wrd_i])
            if wiki_resp.status_code == 200:
                self._html[wrd_i][lang] = bs(wiki_resp.content, 'lxml')
                parse_check += self.wikiContent(lang=lang, wrd_i=wrd_i) # extract only interesting things
        # if both languages parsed correctly, parse_check shall be = 2
        # but also shall be enough if only one parsed
        if parse_check == 0:
            self._html[wrd_i]['pl'] = ''
            self._html[wrd_i]['ru'] = ''
            return

        # if pl wiki, extract data
        if self._html[wrd_i]['pl']:
            self._extractTranslation(wrd_i=wrd_i)
            self._extractDeclination_pl(wrd_i=wrd_i)
            self._extractExample(wrd_i=wrd_i)
        # if ru wiki, extract data
        if self._html[wrd_i]['ru']:
            self._extractDeclination_ru(wrd_i=wrd_i)
        
        return self.formatAll(wrd_i)

    def _removeAcc(self,wrd):
        '''remove accent symbols
        conv to lowercase
        '''
        newWrd = ''
        forbiden_chr = self._makeList("33:47,58:64,91:96,123:126,769")
        for str in wrd:
            if ord(str) not in forbiden_chr:
                newWrd += str
        return newWrd.lower()

    def _makeList(self, rngs):
        lst = []
        for rng in rngs.split(','):
            x = rng.split(':')
            x = [int(i) for i in x]
            if len(x) == 2:
                lst.extend(list(range(x[0],x[1]+1)))
            else:
                lst.append(x[0])
        return lst

    def _extractTranslation(self, wrd_i):
        trans = bs("<div><h3>znaczenia</h3></div>",'lxml')
        html = self._html[wrd_i]['pl']

        def rightDlTag(tag):
            return tag.name == 'dl' and tag.find('span',class_='fld-znaczenia')

        def nextCatDlTag(tag):
            # categgory starts with <dl><dt><span class=
            return tag.name == 'dt' and tag.find('span', class_=True)

        dlTag = self._html[wrd_i]['pl'].find(rightDlTag)
        for sib in dlTag.next_siblings:
            if sib.find(nextCatDlTag): # all siblings down to next <dl> with <dt> and class
                break
            new_tag = html.new_tag(sib.name)
            [new_tag.append(copy.copy(sub_tag)) # tag can (and mostly have) few sub_tags so need to iterate
                for sub_tag in sib.contents if sub_tag.name is not None]
            trans.div.append(new_tag)

        # remove href links
        for aTag in trans.find_all('a'):
            aTag.unwrap()
        
        # if nothing found, set empty str
        if trans.text == 'znaczenia':
            trans = ''
        
        self.data[wrd_i]['translation'] = copy.copy(trans)

    def _extractDeclination(self, wrd_i):
        '''Take declination from ru and pl
        take which avilable or merge.
        If not a table, create a table, translate russian case
        '''
        pass

    def _extractDeclination_pl(self, wrd_i):
        decli = bs("<div><h3>odmiana</h3></div>",'lxml')
        html = self._html[wrd_i]['pl']

        def rightDlTag(tag):
            return tag.name == 'dl' and tag.find('span',class_='fld-odmiana')

        dlTag = html.find(rightDlTag)
        for ddTag in dlTag.find_all('dd'):
            decli.div.append(copy.copy(ddTag))
        
        # remove href links
        for aTag in decli.find_all('a'):
            aTag.unwrap()

        # if nothing found, set empty str
        if decli.text == 'odmiana':
            decli = ''
        
        self.data[wrd_i]['declination_pl'] = copy.copy(decli)

    def _extractDeclination_ru(self, wrd_i):
        decli = bs("<div><h3>odmiana</h3></div>",'lxml')
        html = self._html[wrd_i]['ru']

        def tdWithClass(tag):
            return tag.name == 'td' and tag.has_attr('class')

        # unfortunatelly we need to make negative selection
        # reject table with list<li> or with <td> and class=*
        tableTag = [tag for tag in html.find_all('table') 
                        if not tag.find(tdWithClass) 
                            and not tag.find('li')]
        if len(tableTag) > 0:
            decli.div.append(tableTag[0])
        
        # remove href links
        for aTag in decli.find_all('a'):
            aTag.unwrap()

        # remove <sup> tag with content
        for supTag in decli.find_all('sup'):
            supTag.decompose()

        # if nothing found, set empty str
        if decli.text == 'odmiana':
            decli = ''

        self.data[wrd_i]['declination_ru'] = copy.copy(decli)

    def _extractExample(self, wrd_i):
        exa = bs("<div><h3>przykłady</h3></div>",'lxml')
        html = self._html[wrd_i]['pl']

        def rightDlTag(tag):
            return tag.name == 'dl' and tag.find('span',class_='fld-przyklady')

        dlTag = html.find(rightDlTag)
        for ddTag in dlTag.find_all('dd'):
            exa.div.append(copy.copy(ddTag))

        # remove href links
        for aTag in exa.find_all('a'):
            aTag.unwrap()
        
        # if nothing found, set empty str
        if exa.text == 'przykłady':
            exa = ''
        self.data[wrd_i]['example'] = copy.copy(exa)

    def checkWiki(self, wrd, lang=['pl','ru']):
        ''' check if page exist (ask for HEAD only without downloading whole page)
        it requires for ANY of wiki exist (pl or ru). Still can happen that
        only ru exist but without declination or frazeology so info is zero....lower()
        return null. check self.wrd if success, or '' if fail
        '''
        # to avoid repetition
        for wrd_n in wrd:
            if self._removeAcc(wrd_n) in self.wrd:
                return
        #  reset old data, start search again
        self.__init__()
        wiki_resp_ru = 0
        wiki_resp_pl = 0
        for wrd_n in wrd:
            # prepare correct length list
            self._html.append(copy.copy(self._html_it))
            self.data.append(copy.copy(self.data_it))
            # remove accent from wrd
            wrd_n = self._removeAcc(wrd_n)
            
            if 'pl' in lang and wrd_n:
                wiki_resp_pl = requests.head(self._url['pl'] + wrd_n)
                wiki_resp_pl = wiki_resp_pl.status_code
            if 'ru' in lang and wrd_n:
                wiki_resp_ru = requests.head(self._url['ru'] + wrd_n)
                wiki_resp_ru = wiki_resp_ru.status_code
            if wiki_resp_pl == 200 or wiki_resp_ru == 200:
                self.wrd.append(wrd_n)
            else:
                self.wrd.append('')

    def formatAll(self, wrd_i):
        wiki = bs("<div><h2></h2></div>",'lxml')
        data = self.data[wrd_i]
        wiki.h2.string = self.wrd[wrd_i]
        wiki.div.append(copy.copy(data['translation']))
        wiki.div.append(copy.copy(data['declination_pl']))
        wiki.div.append(copy.copy(data['declination_ru']))
        wiki.div.append(copy.copy(data['example']))

        return wiki.prettify()

    def wikiContent(self, lang, wrd_i):
        '''Find only content (removing menus etc.)
        Aditionally, the word can be in more than one lang, so need to find ru part of wiki
        for pl wiki:
            find <h2> with span where class=lang-code-ru 
            then keep below tags down to next <h2>
        for ru wiki:
            find <h1> with span where id=Русский
            then keep only tags down to next <h1>
        '''
        if lang == 'pl':
            h = 'h2'
            def right_hTag(tag):
                return tag.name == 'h2' and tag.find('span',class_='lang-code-ru')
        else:
            h = 'h1'
            def right_hTag(tag):
                return tag.name == 'h1' and tag.find('span',id='Русский')

        source = self._html[wrd_i][lang].find('div',class_='mw-parser-output') # taking only interesting content, skipping, menus etc.
        html = bs("<div></div>",'lxml') # here we store what interesting
        try:
            hTag = source.find(right_hTag)
        except:
            # something is wrong:
            return 0 # fail
        
        for tag in hTag.next_siblings:
            if tag.name == h:
                break
            if tag.name is not None:
                #  need to create new tag 'couse appending tag directly will destroy new_siblings generator
                new_tag = html.new_tag(tag.name)
                [new_tag.append(copy.copy(sub_tag)) # tag can (and mostly have) few sub_tags so need to iterate
                    for sub_tag in tag.contents if sub_tag.name is not None]
                html.div.append(new_tag)
        
        self._html[wrd_i][lang] = html

        return 1 # success
    