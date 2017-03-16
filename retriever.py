#! /usr/bin/env python
from os import getcwd
from os.path import join, splitext
from sys import argv
from collections import namedtuple

import lucene
from java.nio.file import Paths
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.search.highlight import QueryScorer, SimpleSpanFragmenter, Highlighter, \
    SimpleHTMLFormatter, TokenSources


from analyzer import Analyzer
from indexer import DEFAULT_INDEX_DIR

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


def build_searcher(index_dir=DEFAULT_INDEX_DIR):
    storage = SimpleFSDirectory(Paths.get(index_dir))
    return IndexSearcher(DirectoryReader.open(storage))


class Result(object):
    def __init__(self, file_name, path, fragments):
        self.name, self.extension = splitext(file_name)
        self.path = path.split('/')[1:]  # ignore root doc
        self.fragments = [unicode(f) for f in fragments]

def find_results(query, searcher):
    """
    For the given `query`, search the index against the 'content' field in the index.
    """
    parsed = QueryParser('content', Analyzer()).parse(query)
    highlighter = build_highlighter(parsed)

    score_docs = searcher.search(parsed, MAX_N_DOCS).scoreDocs
    results = []

    for score_doc in score_docs:
        doc = searcher.doc(score_doc.doc)

        content = doc.get('content')
        stream = TokenSources.getTokenStream('content', content, Analyzer())
        fragments = highlighter.getBestTextFragments(stream, content,
                        MERGE_CONTIGUOUS_FRAGMENTS, MAX_N_FRAGMENTS)

        results.append(Result(
            doc.get('name'),
            doc.get('path'),
            fragments
        ))

    return parsed, results


if __name__ == '__main__':
    if len(argv) < 2:
        print 'usage: indexer.py <query>'
        exit(1)

    index_dir = DEFAULT_INDEX_DIR
    if len(argv) >= 3:
        index_dir = argv[2]

    lucene.initVM()
    print find_results(query=argv[1],
                       searcher=index_dir)
