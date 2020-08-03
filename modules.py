import os
import random
import re  # include sub method to use regex
import sqlite3
import sys
import pandas as pd


class Dictionary:
    """store pairs of words as pandas.DataFrame
    
    can add or print a pair of words
    parse input and check if correct
    """

    def __init__(self):
        self.db = pd.DataFrame(columns=['ru', 'pl', 'try_n', 'fail_n'])
        self.db_temp = pd.DataFrame(columns=['ru', 'pl'])
        self.err = ''
        self.history = [0]
        self.history_index = 0

    def importTXT(self, words):
        """allowed input formats:
        "пожаловать		Witamy", str,  words separated with white characters
        list of strings as above, result of file.readlines()
        """
        
        self.err = ''
        if type(words) == list:
            for w in words:
                if type(w) == str:
                    self.__add_str__(w)
                else:
                    self.err += f'IMPORT: Can process only strings, instead found {type(w)}\n'
        elif type(words) == str:
            self.__add_str__(words)
        else:
            self.err += f'Not allowed type {type(words)}\n'
        self.db_temp.reset_index(inplace=True, drop=True)
        # remove rows already existing in self.db
        rows = pd.merge(self.db, self.db_temp, how='right', indicator=True)
        rows = rows['_merge'] == 'right_only'
        len_raw = len(self.db_temp)
        self.db_temp = self.db_temp[rows]
        len_fin = len(self.db_temp)
        dup_no = len_raw - len_fin
        if dup_no:  # If there are duplicates...
            self.err += f'Number of duplicates: {len_raw - len_fin}\n'
        if not self.err:
            self.err = 'No errors'
        return self.db_temp.to_string()

    def commit(self):
        self.db = self.db.append(self.db_temp, ignore_index=True)
        self.db.drop_duplicates(inplace=True)
        self.db.reset_index(inplace=True, drop=True)
        self.db = self.db.fillna(0)

    def __add_str__(self, words):
        line = self.__parse_str__(words)
        if line:
            # line += [0, 0]
            line_s = pd.Series(line, index=self.db_temp.columns)
            self.db_temp = self.db_temp.append(line_s, ignore_index=True)
            self.db_temp.drop_duplicates(inplace=True)

    def __parse_str__(self, line):
        line = line.strip()  # remove space at beginning and at the end
        if line.count('\s') == 1:  # if only one space, it's easy
            return line.split()
        line = re.sub(r'(?<! ) (?! )', '_', line)  # single spaces replace with '_' to keep two-words combos together
        words = line.split()  # all other whitespaces separate the translation
        if len(words) != 2:
            if words:  # don't need to report empt lines []
                self.err += f'More or less than two words: {words}\n'
            return ''
        words = [w.replace('_', ' ') for w in words]  # don't need underscore anymore
        return words

    def print(self, line_no=-1) -> pd.Series:
        """return row from DB

        Requires row number. If empty, will return random row.
        To return current row use self.history and self.history_index
        """
        
        if self.db.empty:  # in case empty DB
            return ''  # reciver must handle empty string
        if line_no == -1:  # return rand line
            random.seed()
            mid_hits = max(self.db.try_n) // 2  # rand only from numbers with try count less than half of max
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
        db_file = sqlite3.connect(file)
        self.db = pd.read_sql_query("SELECT * FROM dic", db_file)
        #  TODO: check if proper file and properly opened
        self.history = [0]
        self.history_index = 0

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
        self.db.drop(self.db.index[row_no])



class FileSystem:
    """Handles all file system stuff

    Define file path and names. For each type stores as list of path, name and extensions:\n
    -imported TXT file:          self._fileTXT, access through self.getTXT\n
    -temporary words.mp3 file:   self._fileMP3, access through self.getMP3\n
    -DB file:                    self._fileDB, access through self.getDB\n
    -aplication location:        self._fileAPP, access through self.getAPP\n

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
        self._fileMP3 = ['', 'word', '.mp3']  # name is constant, path will be taken from self._fileAPP
        self.typeIMP = ['text', '.txt']
        self.typeDB = ['SQlite3', '.s3db']
        
        self.setAPP()
        self._fileMP3[self._PATH] = self._fileAPP[self._PATH]
    
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
        """input typical for QtFileDialog: ('/..../dic_empty.txt', 'SQlite3 (*.s3db)')
        """
        # override file extension. No other than s3db can be opened
        self._fileDB = self._split_path(path[0])
        self._fileDB[self._EXT] = self.typeDB[1]


    def getDB(self, path_only=False, file_only=False, ext_type=False):
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
