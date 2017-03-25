from __future__ import unicode_literals

from org.apache.pylucene.analysis import PythonAnalyzer
from org.apache.lucene.analysis.standard import StandardTokenizer, StandardFilter
from org.apache.lucene.analysis import LowerCaseFilter, StopFilter
from org.apache.lucene.analysis.miscellaneous import ASCIIFoldingFilter
from org.apache.lucene.analysis.ro import RomanianAnalyzer
from org.tartarus.snowball.ext import RomanianStemmer
from org.apache.lucene.analysis.snowball import SnowballFilter
from java.io import StringReader
from org.apache.lucene.analysis.tokenattributes import CharTermAttribute


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


# pe langa rezultate:
# pt toti termenii din intrebare, idf-ul lor
# in document, in paranteza tf-ul lui


def tokenize(word):
    stream = Analyzer().tokenStream('content', StringReader(word))
    stream.reset()
    stream.incrementToken()
    return stream.getAttribute(CharTermAttribute.class_).toString()

