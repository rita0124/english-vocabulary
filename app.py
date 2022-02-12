import csv
import requests
from bs4 import BeautifulSoup


def read_vocabs():
    vocabs = []
    with open('original_english.csv', 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        for line in reader:
            vocabs.append(line[1])
    print(vocabs)
    return vocabs

def query_word(word):
    url = f'https://cdict.net/?q={word}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    line = soup.find('meta', {"name":"description"})
    # line:  <meta content="boat 船(vi.)乘船(vt.)以船運" name="description"/>
    word = line.get('content')
    return word

if __name__ == '__main__':
    read_vocabs()
