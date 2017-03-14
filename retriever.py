#! /usr/local/bin/python

from os import getcwd
from os.path import join
from sys import argv

import lucene
from java.nio.file import Paths
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.store import SimpleFSDirectory

from indexer import INDEX_LOCATION, build_analyzer

MAX_N_DOCS = 50


def find_results(query, store_dir):
    """
    For the given `query`, search the index against the 'content' field in the index.
    """
    storage = SimpleFSDirectory(Paths.get(store_dir))
    parsed = QueryParser('content', build_analyzer()).parse(query)
    print 'Parsed query:', str(parsed).replace('content:', '')

    searcher = IndexSearcher(DirectoryReader.open(storage))
    score_docs = searcher.search(parsed, MAX_N_DOCS).scoreDocs
    print '%d matching documents:' % len(score_docs)

    for score_doc in score_docs:
        doc = searcher.doc(score_doc.doc)
        print '  ', doc.get('name'),
        print '(in %s)' % doc.get('path')


if __name__ == '__main__':
    if len(argv) < 2:
        print 'usage: indexer.py <query>'
        exit(1)

    lucene.initVM()

    find_results(query=argv[1],
                 store_dir=join(getcwd(), INDEX_LOCATION))
