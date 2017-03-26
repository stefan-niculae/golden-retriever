# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from unicodedata import normalize
import re

from org.apache.pylucene.analysis import PythonAnalyzer
from org.apache.lucene.analysis.standard import StandardTokenizer, StandardFilter
from org.apache.lucene.analysis import LowerCaseFilter, StopFilter
from org.apache.lucene.analysis.miscellaneous import ASCIIFoldingFilter
from org.apache.lucene.analysis.ro import RomanianAnalyzer
from org.tartarus.snowball.ext import RomanianStemmer
from org.apache.lucene.analysis.snowball import SnowballFilter
from org.apache.lucene.analysis.tokenattributes import CharTermAttribute
from java.io import StringReader


class Analyzer(PythonAnalyzer):
    def createComponents(self, _):
        tokenizer = StandardTokenizer()
        stream = StandardFilter(tokenizer)

        # Order of filtering is important
        stream = LowerCaseFilter(stream)  # case independent
        stream = ASCIIFoldingFilter(stream)  # convert diacritics
        stream = self.filter_stopwords(stream)  # ignore stopwords
        stream = SnowballFilter(stream, RomanianStemmer())  # stemming

        return self.TokenStreamComponents(tokenizer, stream)

    @staticmethod
    def filter_stopwords(stream):
        stream = StopFilter(stream, RomanianAnalyzer.getDefaultStopSet())
        with open('romanian-stopwords.txt') as f:
            additional_stopwords = unicode(f.read(), 'utf-8').split()
        additional_stopwords = StopFilter.makeStopSet(additional_stopwords)
        return StopFilter(stream, additional_stopwords)


def tokenize(word):
    stream = Analyzer().tokenStream('content', StringReader(word))
    stream.reset()
    stream.incrementToken()
    return stream.getAttribute(CharTermAttribute.class_).toString()


def transform(query):
    """
    >>> transform('si')
    <strike>si</strike>
    >>> transform('și')
    <strike>și</strike>
    >>> transform('mama')
    <b>mam</b>a
    >>> transform('mamă')
    <b>mam</b>ă
    >>> transform('mamelor')
    <b>mam</b>elor
    >>> transform('coteț')
    <b>cotet</b>
    >>> transform('si si și')  # not twice
    <strike>si</strike> <strike>si</strike> <strike>si</strike>
    >>> transform('o portocala')  # whole words only
    <strike>o<strike> <b>portocal</b>a
    >>> transform('o mamă are o fată care manancă o portocală')
    <strike>o</strike> <b>mam</b>a are <strike>o</strike> <b>fat</b>a care <b>mananc</b>a <strike>o</strike> <b>portocal</b>a
    >>> transform('la o atunci')
    <strike>la</strike> <strike>o</strike> <strike>atunci</strike>
    """
    query = normalize('NFKD', query).encode('ascii', 'ignore')
    transformed_terms = set()
    for word in query.split():
        term = tokenize(word)
        if term == '':
            query = re.sub(r'\b%s\b' % word, '<strike>%s</strike>' % word, query)
        elif term not in transformed_terms:
            query = query.replace(term, '<b>' + term + '</b>')
            transformed_terms.add(term)

    return query
