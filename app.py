import os
import csv
import json
import requests
from bs4 import BeautifulSoup
from random import randrange


class VocabBot():

    def __init__(self):
        self.pushed = self.read_sent_index()
        self.vocabs = self.read_vocabs()
        self.ch_vocabs = self.read_ch_vocabs()
        self.jp_vocabs = self.read_jp_vocabs()
        self.pronunce_sentence = None

    def gen_last_answer(self):
        # Show the en and ch voc
        # last_pushed_index
        vid = self.pushed[-1] - 1
        speak_jp_word = self.jp_vocabs[vid].split('; ')[0]
        ans = f'{self.jp_vocabs[vid]}\n'
        ans += f'【發音】{self.gen_pronun_jp(speak_jp_word)}\n'
        ans += f'【例句】{self.pronunce_sentence}\n'
        ans += f'【字典】https://jisho.org/search/{speak_jp_word}\n'
        ans += f'【中文】{self.ch_vocabs[vid]}\n'
        return ans

    def gen_new_question(self):
        # Show the en
        vid = randrange(len(self.vocabs)) + 1
        while vid in self.pushed:
            vid = randrange(len(self.vocabs)) + 1
        #self.pushed.append(vid)
        with open('pushed.txt', 'a') as f:
            f.write(f'{vid}\n')
        return self.vocabs[vid - 1]

    def read_sent_index(self):
        pushed = []
        with open('pushed.txt', 'r') as f:
            lines = f.readlines()
        for line in lines:
            pushed.append(int(line))
        #print(pushed)
        return pushed

    def read_ch_vocabs(self):
        ch_vocabs = []
        with open('vocabulary_cdict.csv', 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            for line in reader:
                ch_vocabs.append(line[2])
        return ch_vocabs

    def read_jp_vocabs(self):
        jp_vocabs = []
        with open('vocabulary_jisho.csv', 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            for line in reader:
                jp_vocabs.append(line[2])
        return jp_vocabs

    def read_vocabs(self):
        vocabs = []
        with open('original_english.csv', 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            for line in reader:
                vocabs.append(line[1])
        #print(vocabs)
        return vocabs

    # Ask soup
    # https://jisho.org/search/{word}
    def get_soup_jisho(self, word):
        url = f'https://jisho.org/search/{word}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup

    # Search Chinese on cdict
    def query_word(word):
        url = f'https://cdict.net/?q={word}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        line = soup.find('meta', {"name":"description"})
        # line:  <meta content="boat 船(vi.)乘船(vt.)以船運" name="description"/>
        word = line.get('content')
        return word

    # Search Japanese on jisho
    def query_word_jp(self, word):
        soup = self.get_soup_jisho(word)
        block = soup.find('div', {"class": "concept_light-representation"})

        # Sorry, couldn't find any words matching appreciable.
        if not block:
            return

        # Because there might be only 平片假名 / 漢字 show pronunce
        # 先處理上標 用空格分開發音
        # spells = block.find_all('span', {'class', 'kanji'})
        # if spells:
        #     pronun = ' '.join(spell.string for spell in spells)
        # 上用法無法處理 backscratcher 孫の手 まごのて becomes まごて
        spells = block.find_all('span',{"class":"furigana"})[0].select('span')
        pronun = '' # prepare for Upper text
        # The scaned down word / meet becomes ['出会', 'う']
        # So we have to combine those down word
        present = ''.join(list(block.find(
            'span', { 'class', 'text' }).stripped_strings))
        for i, spell in enumerate(spells):  # soup in soups
            if spell.has_attr('class'):
                pronun += f'{spell.getText()}'
            else:
                pronun += f'{present[i]}'

        # Hiragana / Katakana
        # 下標字合體
        down_spell = ''.join(present)

        # Combine
        if pronun and down_spell:
            word = f'{down_spell}; {pronun}'
        else:
            word = ''.join([down_spell, pronun])

        return word

    # Search Japanese on jisho
    def query_sentence_jp(self, word):
        soup = self.get_soup_jisho(word)
        block = soup.find('div', {"class": "sentence_content"})

        # Sorry, couldn't find any words matching appreciable.
        if not block:
            print('not block!!')
            return

        # 包含漢字的句子切片
        sentence_block = block.find_all( 'span', { 'class', 'unlinked' } )
        sentence = ''
        for s in sentence_block:
             sentence += s.getText()
        # 句子中出現的片假名
        pronun_block = block.find_all( 'span', { 'class', 'furigana' } )
        words = []
        for word_block in pronun_block:
            words.append(word_block.getText())
        sentence_info = {
                'sentence': sentence,
                'words': words }
        if sentence_info:
            return sentence_info

    def gen_pronun_jp(self, word):
        url = 'https://ttsmp3.com/makemp3_new.php'
        print(f'--> {word}')
        sentence_dict = self.query_sentence_jp(word)
        # To prevent like 複雑さ do not get any sentence
        # but in querying in english
        sentence_dict = self.query_sentence_jp(word)
        # There might return None since no sentence
        if sentence_dict is not None:
            sentence = sentence_dict['sentence']
        else:
            sentence = 'no example sentence'
        words = ''
        if sentence_dict is not None:
            for w in sentence_dict['words']:
                words += f', 〖{w}〗'
        sentence += words
        pronun = ''
        pronun += f'{word}, '
        pronun += f'{sentence}'
        payload = {'msg': pronun, 'lang':'Takumi', 'source':'ttsmp3'}
        resp = json.loads(requests.post(url, data=payload).text)
        self.pronunce_sentence = pronun
        return resp['URL']

    def send_message(self):
        # radish
        headers = {
                'Authorization': os.environ.get('DriverSecret_1')
                }
        # driver
        headers2 = {
                'Authorization': os.environ.get('DriverSecret_2')
                }
        last = self.gen_last_answer()
        voca = self.gen_new_question()
        #print(f'Last: {last}')
        #print(f'New: {voca}')
        mess = f'\n【解答】{last}\n\n'
        mess += f'【題目】{voca}\n'
        mess += f'【發音】https://s.yimg.com/bg/dict/dreye/live/f/{voca}.mp3'
        data = {
                'message': mess
                }
        r = requests.post(
                'https://notify-api.line.me/api/notify',
                headers=headers,
                data=data)
        r = requests.post(
                'https://notify-api.line.me/api/notify',
                headers=headers2,
                data=data)
        print(data)

if __name__ == '__main__':
    vbot = VocabBot()
    #print(vbot.gen_last_answer())
    vbot.send_message()
