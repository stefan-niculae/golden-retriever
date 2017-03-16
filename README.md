# golden-retriever

Information retrieval system for documents in romanian. It supports word stemming, ignores stop words, is case-independent and highlights the terms.

![demo](demo.gif)

## Build
 - install pylucene
 - `pip install textract pdfminer flask`
 - `npm install jquery semantic` and move them to `interface/lib/semantic.css` and `interface/lib/jquery.js`

## Run
1. `./indexer.py`
2. `./server.py`

## Dev
 - `pug`, `coffee`, `sass` for the interface
PyLucene samples: http://svn.apache.org/viewvc/lucene/pylucene/trunk/samples/