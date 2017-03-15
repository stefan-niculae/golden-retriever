from org.apache.pylucene.analysis import PythonAnalyzer
from org.apache.lucene.analysis.standard import StandardTokenizer, StandardFilter
from org.apache.lucene.analysis import LowerCaseFilter, StopFilter
from org.apache.lucene.analysis.ro import RomanianAnalyzer
from org.apache.lucene.analysis.snowball import SnowballFilter
from org.tartarus.snowball.ext import RomanianStemmer
from org.apache.lucene.analysis.miscellaneous import ASCIIFoldingFilter


class Analyzer(PythonAnalyzer):
    def createComponents(self, _):
        source = StandardTokenizer()

        stream = StandardFilter(source)
        stream = LowerCaseFilter(stream)  # case independent
        stream = self.filter_stopwords(stream)  # stopwords
        stream = SnowballFilter(stream, RomanianStemmer())  # stemming
        stream = ASCIIFoldingFilter(stream)  # remove diacritics

        return self.TokenStreamComponents(source, stream)

    @staticmethod
    def filter_stopwords(stream):
        stream = StopFilter(stream, RomanianAnalyzer.getDefaultStopSet())
        with open('romanian-stopwords.txt') as f:
            additional_stopwords = unicode(f.read(), 'utf-8').split()
        additional_stopwords = StopFilter.makeStopSet(additional_stopwords)
        return StopFilter(stream, additional_stopwords)
