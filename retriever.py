#! /usr/bin/env python

from __future__ import unicode_literals

from os.path import splitext
from sys import argv
import re
from cgi import escape

import lucene
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.index import DirectoryReader, PostingsEnum, MultiFields, Term
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search import IndexSearcher, BooleanQuery, BooleanClause, BoostQuery
from org.apache.lucene.search.highlight import QueryScorer, SimpleSpanFragmenter, Highlighter, \
    SimpleHTMLFormatter, TokenSources
from org.apache.lucene.util import BytesRef
from org.apache.lucene.search.similarities import ClassicSimilarity
from java.nio.file import Paths

from analyzer import Analyzer, tokenize, transform
from indexer import DEFAULT_INDEX_DIR

MAX_N_DOCS = 50
FRAGMENT_SIZE = 150
MAX_N_FRAGMENTS = 50
MAX_DOC_CHARS_TO_ANALYZE = 1000000
MERGE_CONTIGUOUS_FRAGMENTS = True

ABSTRACT_BOOST = .06  # how many times bigger log(abstract_score) should be over log(content_score)
CONTENT_BOOST  = 1.


def build_highlighter(parsed_query):
    scorer = QueryScorer(parsed_query, 'content')
    highlighter = Highlighter(SimpleHTMLFormatter(), scorer)
    fragmenter = SimpleSpanFragmenter(scorer, FRAGMENT_SIZE)
    highlighter.setTextFragmenter(fragmenter)
    return highlighter


def build_reader(index_dir=DEFAULT_INDEX_DIR):
    storage = SimpleFSDirectory(Paths.get(index_dir))
    return DirectoryReader.open(storage)


def stats_tooltip(word, doc_id, reader):
    # content statistics
    term = Term('content', tokenize(word))
    term_text = unicode(term).replace('content:', '')
    doc_count = reader.docFreq(term)  # in how many docs the term appears

    total_term_count = reader.totalTermFreq(term)  # how many times the term appears in any doc
    n_docs = reader.getDocCount('content')  # total number of docs

    postings = MultiFields.getTermDocsEnum(reader, 'content', BytesRef(term_text))
    while postings.docID() != doc_id:  # this is bad
        postings.nextDoc()
    term_count = postings.freq()  # how many times the term appears in this doc

    similarity = ClassicSimilarity()
    tf   = similarity.tf(float(term_count))  # sqrt(term_freq)
    # whether the term is is common or rare among all the docs
    idf   = similarity.idf(long(doc_count), long(n_docs))  # log((n_docs+1)/(doc_count+1)) + 1

    # abstract statistics
    abstract_term = Term('abstract', tokenize(word))
    abstract_doc_count = reader.docFreq(abstract_term)
    abstract_total_term_count = reader.totalTermFreq(abstract_term)
    a_idf = similarity.idf(long(abstract_doc_count), long(n_docs))

    abstract_postings = MultiFields.getTermDocsEnum(reader, 'abstract', BytesRef(term_text))
    if not abstract_postings:  # the term appears in no document's abstract
        abstract_term_count = 0
        a_tf = 1
    else:
        while abstract_postings.docID() != doc_id:  # this is bad
            if abstract_postings.nextDoc() == abstract_postings.NO_MORE_DOCS:
                abstract_term_count = 0  # it does not appear in this document's abstract
                a_tf = 1
                break
        else:  # no break, it does appear in this document's abstract
            abstract_term_count = abstract_postings.freq()
            a_tf = similarity.tf(float(abstract_term_count))

    content_score  = tf   * idf   ** 2 * CONTENT_BOOST
    abstract_score = a_tf * a_idf ** 2 * ABSTRACT_BOOST

    # mixing concerns like nobody's business
    return '''
            <div class="popup">
                <div class="term">{}</div>     
                
                <table>
                <tr>
                    <th> </th>
                    <th>abstr</th>
                    <th>body</th>
                    <th>total</th>
                </tr>
                
                <tr><td>this doc</td>   <td>{}</td>     <td>{}</td>     <td>{}</td>     </tr>
                <tr><td>TF</td>         <td>{:.2g}</td> <td>{:.2g}</td> <td>{:.2g}</td> </tr>
                
                <tr><td>nr docs</td>    <td>{}</td>     <td>{}</td>     <td>{}</td>     </tr>
                <tr><td>IDF</td>        <td>{:.2g}</td> <td>{:.2g}</td> <td>{:.2g}</td> </tr>
                
                <tr><td>score</td>      <td>{:.2g}</td> <td>{:.2g}</td> <td><b>{:.2g}</b></td> </tr>
                <tr><td>all docs</td>   <td>{}</td>     <td>{}</td>     <td>{}</td>     </tr>
                </table>
                
                <div class="total-docs">{}</div>
            </div>
            '''.format(term_text,

                       abstract_term_count, term_count - abstract_term_count, term_count,
                       a_tf, tf, a_tf * tf,

                       abstract_doc_count, doc_count, doc_count,
                       a_idf, idf, a_idf * idf,

                       abstract_score, content_score, abstract_score * content_score,

                       abstract_total_term_count, total_term_count - abstract_total_term_count, total_term_count,

                       n_docs
                       )


class Result(object):
    # the default html highlighter wraps results in <b> tags
    highlighted = re.compile(r'<B>(\w+)</B>', re.UNICODE)

    def __init__(self, file_name, path, fragments, doc_id, reader):
        self.name, self.extension = splitext(file_name)
        self.path = path.split('/')[1:]  # ignore root doc

        self.fragments = []
        for frag in fragments:
            highlights = set(Result.highlighted.findall(frag))
            for word in highlights:
                tooltip = stats_tooltip(word, doc_id, reader)
                frag = frag.replace('<B>' + word,
                                    '<B data-html=\'%s\'>' % escape(tooltip) + word)
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
    content_query  = QueryParser('content',  Analyzer()).parse(query)
    highlighter = build_highlighter(content_query)

    abstract_query = QueryParser('abstract', Analyzer()).parse(query)
    abstract_query = BoostQuery(abstract_query, ABSTRACT_BOOST)  # boost the abstract
    content_query  = BoostQuery(content_query,  CONTENT_BOOST)

    # query on both the abstract and the content field
    query_builder = BooleanQuery.Builder()
    query_builder.add(abstract_query, BooleanClause.Occur.SHOULD)
    query_builder.add(content_query,  BooleanClause.Occur.MUST)
    query = query_builder.build()

    hits = searcher.search(query, MAX_N_DOCS).scoreDocs
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

    return results


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

    print 'parsed query:', transform(query)
    print 'results:\n', '\n\n'.join(unicode(r) for r in results)


if __name__ == '__main__':
    main()
