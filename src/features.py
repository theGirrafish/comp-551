import os
import re
import json
import numpy as np

from pathlib import Path
from itertools import chain
from collections import Counter

from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk import download as nltk_download


class PreprocessData:

    NUM_TOP_WORDS = 160
    LEXICON = 'vader_lexicon'
    PUNCTUATION_REGEX = "[^\w'_]+"
    DATA_PATH = './data/proj1_data.json'
    CURSE_WORDS_PATH = './data/curse_words.txt'
    TOP_WORDS_PATH = './words.txt'


    def __init__(self):
        with open(self.DATA_PATH) as f:
            data = json.load(f)

        self.data = data
        self.pdata = data
        self.X = []
        self.y = []


    def preprocess_data(self, data):
        # train_set = data[:10000]
        # validation_set = data[10000:11000]
        # test_set = data[11000:]

        # DEBUG
        train_set = data[:100]
        validation_set = data[100:110]
        test_set = data[110:120]

        for dp in train_set:
            dp['split_text'] = dp['text'].lower().split()
            dp['np_regex'] = re.split(self.PUNCTUATION_REGEX, dp['text'].lower())
            dp['is_root'] = 1 if dp['is_root'] else 0

        return train_set, validation_set, test_set


    def initialize(self, data):
        for dp in data:
            self.X.append([dp['children'], dp['controversiality'], dp['is_root']])
            self.y.append(dp['popularity_score'])


    def split_data(self, data):
        # return data[:10000], data[10000:11000], data[11000:]
        return data[:100], data[100:110], data[110:120]


    def compute_most_common_words(self, data, regex=False):
        word_count = Counter()
        for dp in data:
            word_count += Counter(dp['split_text']) if not regex else Counter(dp['np_regex'])

        top_words = [w[0] for w in word_count.most_common(self.NUM_TOP_WORDS)]
        with open(self.TOP_WORDS_PATH, 'w+') as f:
            f.writelines(f'{word}\n' for word in top_words)


    def feature_most_common_words(self, data):
        with open(self.TOP_WORDS_PATH, 'r+') as f:
            top_words = f.readlines()

        most_common = []
        for dp in data:
            text = Counter(dp['text'])
            most_common.append([text.get(word, 0) for word in top_words])

        return most_common


    def feature_num_capitals(self, data):
        return [sum(1 for c in dp['text'] if c.isupper()) for dp in data]


    def feature_sentiment(self, data):
        return [self.sentiment_analysis(dp['text'])['compound'] for dp in data]


    def feature_curse_words(self, data):
        curse_words = self.load_swears(self.CURSE_WORDS_PATH)
        return [self.count_swears(dp['np_regex'], curse_words) for dp in data]


    def feature_num_words(self, data):
        return [len(dp['np_regex']) for dp in data]


    def compute_features(self, data):
        self.initialize(data)

        top_words = self.feature_most_common_words(data)
        num_capitals = self.feature_num_capitals(data)
        sentiment = self.feature_sentiment(data)
        curse_words = self.feature_curse_words(data)
        num_words = self.feature_num_words(data)

        for i, x in enumerate(self.X):
            x += top_words[i]
            x.append(num_capitals[i])
            x.append(sentiment[i])
            x.append(curse_words[i])
            x.append(num_words[i])

        X = np.array(self.X)
        y = np.array(self.y)

        return X, y

    def check_lexicon(self):
        if not os.path.exists(os.path.join(Path.home(), f'nltk_data/sentiment/{self.LEXICON}.zip')):
            nltk_download('vader_lexicon')

    def sentiment_analysis(self, text):
        self.check_lexicon()

        sia = SentimentIntensityAnalyzer()
        ss = sia.polarity_scores(text)
        return ss

    def load_swears(self, path):
        with open(self.CURSE_WORDS_PATH) as f:
            swears = f.readlines()
        return swears

    def count_swears(self, words, swears):
        num_swears = sum(1 for w in words if w in swears)


ppd = PreprocessData()
train, validation, test = ppd.preprocess_data(ppd.data)
ppd.compute_most_common_words(train)
X, y = ppd.compute_features(train)
print(X.shape)
print(y.shape)
