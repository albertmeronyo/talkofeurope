#!/usr/bin/env python

from SPARQLWrapper import SPARQLWrapper, JSON
import csv
import cStringIO
import codecs

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

 
sparql = SPARQLWrapper("http://linkedpolitics.ops.few.vu.nl/sparql/")

# Time range of complete years
time_range = range(2000, 2013)

for year in time_range:
    sparql.setQuery("""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX lp: <http://purl.org/linkedpolitics/vocabulary/>
    PREFIX lp_eu: <http://purl.org/linkedpolitics/vocabulary/eu/plenary/>
    PREFIX ns1: <http://xmlns.com/foaf/0.1/>
    PREFIX ns2: <http://www.w3.org/2002/07/owl#>
    PREFIX xml: <http://www.w3.org/XML/1998/namespace>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>

    SELECT (COUNT(?agendaitem) AS ?count) ?title
    WHERE {
      ?speech a lp_eu:Speech .
      ?agendaitem lp:hasPart ?speech .
      ?agendaitem lp:title ?title .
      ?agendaitem dc:date ?date .
      FILTER (langMatches(lang(?title), "EN"))
      FILTER (?date >= "%s-01-01"^^xsd:date && ?date <= "%s-12-31"^^xsd:date)
    } 
    GROUP BY ?title
    ORDER BY ?count
    LIMIT 500
    """ % (str(year), str(year)))
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    with open('out-%s.csv' % str(year), 'wb') as csvfile:
        writer = UnicodeWriter(csvfile, delimiter='\t',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['title', 'count'])
        for result in results["results"]["bindings"]:
            writer.writerow([result["title"]["value"],
                             result["count"]["value"]])


