import csv
import requests
from bs4 import BeautifulSoup
from random import randrange


class VocabBot():

    def __init__(self):
        self.pushed = self.read_sent_index()
        self.vocabs = self.read_vocabs()
        self.ch_vocabs = self.read_ch_vocabs()
        self.jp_vocabs = self.read_jp_vocabs()

    def gen_last_answer(self):
        # Show the en and ch voc
        # last_pushed_index
        vid = self.pushed[-1] - 1
        ans = f'self.read_jp_vocabs[vid]\n{self.ch_vocabs[vid]}'
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
    # https://jisho.org/search/{word}
    def query_word_jp(self, word):
        url = f'https://jisho.org/search/{word}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
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

    def send_message(self):
        headers = {
                'Authorization': 'Bearer xxx'
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
        print(data)

if __name__ == '__main__':
    vbot = VocabBot()
    #print(vbot.gen_last_answer())
    vbot.send_message()
