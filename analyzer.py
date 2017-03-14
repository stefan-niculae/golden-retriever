from org.apache.lucene.analysis.miscellaneous import LimitTokenCountAnalyzer
from org.apache.lucene.analysis.standard import StandardAnalyzer


MAX_TOKEN_COUNT = 1048576


def build_analyzer():
    # TODO add stemming, diacritics
    analyzer = StandardAnalyzer()
    return LimitTokenCountAnalyzer(analyzer, MAX_TOKEN_COUNT)  # limit max nr of tokens
