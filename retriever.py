#! /usr/bin/env python

from __future__ import unicode_literals

from os.path import splitext
from sys import argv
import re

import lucene
from java.nio.file import Paths
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.index import DirectoryReader, PostingsEnum, MultiFields, Term
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.search.highlight import QueryScorer, SimpleSpanFragmenter, Highlighter, \
    SimpleHTMLFormatter, TokenSources
from org.apache.lucene.util import BytesRef
from org.apache.lucene.search.similarities import ClassicSimilarity


from analyzer import Analyzer, tokenize
from indexer import DEFAULT_INDEX_DIR

MAX_N_DOCS = 50
FRAGMENT_SIZE = 120
MAX_N_FRAGMENTS = 50
MAX_DOC_CHARS_TO_ANALYZE = 1000000
MERGE_CONTIGUOUS_FRAGMENTS = True


def build_highlighter(parsed_query):
    scorer = QueryScorer(parsed_query, 'content')
    highlighter = Highlighter(SimpleHTMLFormatter(), scorer)
    fragmenter = SimpleSpanFragmenter(scorer, FRAGMENT_SIZE)
    highlighter.setTextFragmenter(fragmenter)
    return highlighter

def build_reader(index_dir=DEFAULT_INDEX_DIR):
    storage = SimpleFSDirectory(Paths.get(index_dir))
    return DirectoryReader.open(storage)


def statistics(word, doc_id, reader):
    postings = MultiFields.getTermDocsEnum(reader, 'content', BytesRef('mam'))
    while postings.docID() != doc_id:  # this is bad
        postings.nextDoc()

    term = Term('content', tokenize(word))
    doc_count = reader.docFreq(term)  # in how many docs the term appears
    term_freq = postings.freq()  # how many times the term appears in this doc

    total_term_freq = reader.totalTermFreq(term)  # how many times the term appears in any doc
    n_docs = reader.getDocCount('content')  # total number of docs

    similarity = ClassicSimilarity()
    tf = similarity.tf(float(term_freq))  # sqrt(term_freq)
    # whether the term is is common or rare among all the docs
    idf = similarity.idf(long(doc_count), long(n_docs))  # log((n_docs+1)/(doc_count+1)) + 1

    return unicode(term).replace('content:', ''), tf, idf, total_term_freq



highlighted = re.compile(r"<B>(\w+)</B>")
class Result(object):
    def __init__(self, file_name, path, fragments, doc_id, reader):
        self.name, self.extension = splitext(file_name)
        self.path = path.split('/')[1:]  # ignore root doc

        self.fragments = []
        for frag in fragments:
            highlights = set(highlighted.findall(frag))
            for word in highlights:
                term, tf, idf, total_term_freq = statistics(word, doc_id, reader)
                tooltip = 'tokenized: {},' \
                          'tf: {:.2g},' \
                          'idf: {:.2g},' \
                          'total term freq: {}'.format(term, tf, idf, total_term_freq)
                frag = frag.replace('<B>' + word,
                                    '<B data-tooltip="{}">{}'.format(tooltip, word))
            self.fragments.append(frag)

    def __unicode__(self):
        return '> {} (in {})\n{}'.format(
            self.name,
            '/'.join(self.path),
            '\n'.join(self.fragments)
        )

def find_results(query, reader):
    """
    For the given `query`, search the index against the 'content' field in the index.
    """
    searcher = IndexSearcher(reader)
    parsed = QueryParser('content', Analyzer()).parse(query)
    highlighter = build_highlighter(parsed)

    hits = searcher.search(parsed, MAX_N_DOCS).scoreDocs
    results = []

    for hit in hits:
        doc = searcher.doc(hit.doc)

        content = doc.get('content')
        stream = TokenSources.getTokenStream('content', content, Analyzer())
        fragments = highlighter.getBestTextFragments(stream, content,
                        MERGE_CONTIGUOUS_FRAGMENTS, MAX_N_FRAGMENTS)
        fragments = [unicode(f).strip() for f in fragments]
        fragments = [f for f in fragments if f != '']  # no empty fragments

        if not ''.join(fragments) == '':
            results.append(Result(
                doc.get('name'),
                doc.get('path'),
                fragments,

                hit.doc,
                reader
            ))

    parsed = unicode(parsed).replace('content:', '')
    return parsed, results


def main():
    if len(argv) < 2:
        print 'usage: retriever.py <query>'
        exit(1)

    index_dir = DEFAULT_INDEX_DIR
    if len(argv) >= 3:
        index_dir = argv[2]

    lucene.initVM()

    query, results = find_results(
        query=argv[1],
        reader=build_reader(index_dir))

    print 'parsed query:', query
    print 'results:\n', '\n\n'.join(unicode(r) for r in results)


if __name__ == '__main__':
    main()
