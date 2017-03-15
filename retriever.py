#! /usr/bin/env python

from os import getcwd
from os.path import join
from sys import argv

import lucene
from java.nio.file import Paths
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.search.highlight import QueryScorer, SimpleSpanFragmenter, Highlighter, \
    SimpleHTMLFormatter, TokenSources


from analyzer import Analyzer
from indexer import INDEX_LOCATION

MAX_N_DOCS = 50
FRAGMENT_SIZE = 20
MAX_N_FRAGMENTS = 50
MAX_DOC_CHARS_TO_ANALYZE = 10000
MERGE_CONTIGUOUS_FRAGMENTS = True


def build_highlighter(parsed_query):
    scorer = QueryScorer(parsed_query, 'content')
    highlighter = Highlighter(SimpleHTMLFormatter(), scorer)
    fragmenter = SimpleSpanFragmenter(scorer, FRAGMENT_SIZE)
    highlighter.setTextFragmenter(fragmenter)
    return highlighter


def find_results(query, store_dir):
    """
    For the given `query`, search the index against the 'content' field in the index.
    """
    storage = SimpleFSDirectory(Paths.get(store_dir))
    parsed = QueryParser('content', Analyzer()).parse(query)
    print 'Parsed query:', str(parsed).replace('content:', '')
    highlighter = build_highlighter(parsed)

    searcher = IndexSearcher(DirectoryReader.open(storage))
    score_docs = searcher.search(parsed, MAX_N_DOCS).scoreDocs
    print '%d matching documents:' % len(score_docs)

    for score_doc in score_docs:
        doc = searcher.doc(score_doc.doc)
        print '  ', doc.get('name'),
        print '(in %s)' % doc.get('path')

        content = doc.get('content')
        stream = TokenSources.getTokenStream('content', content, Analyzer())
        fragments = highlighter.getBestTextFragments(stream, content,
                                                     MERGE_CONTIGUOUS_FRAGMENTS, MAX_N_FRAGMENTS)
        for fragment in fragments:
            print '    ', unicode(fragment).replace('B>', 'mark>')  # default formatter wraps in <B> tags


if __name__ == '__main__':
    if len(argv) < 2:
        print 'usage: indexer.py <query>'
        exit(1)

    lucene.initVM()

    find_results(query=argv[1],
                 store_dir=join(getcwd(), INDEX_LOCATION))
