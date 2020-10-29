---
title: Rediner - Named Entity Analysis in RedisGraph
css: site.css
toc: false
---

This demonstrates of the use of the [RedisGraph](https://oss.redislabs.com/redisgraph/) to
store and analyze named entities (people, places, objects, etc.). The
data collection involves applying a
[Named Entity Recognition](https://en.wikipedia.org/wiki/Named-entity_recognition) (NER)
model from [SpaCy](https://spacy.io) to a set of blog posts.

An example application uses [Flask](https://flask.palletsprojects.com/en/1.1.x/)
and provides you to the ability to navigate
the blog posts via the cooccurrences of the named entityies. It also
provides full text search on the graph and displays the collect of named
entities from the search results. The application has a simple two-tier
architecture where the Flask-based web application uses
[Cypher](https://www.opencypher.org) to directly query RedisGraph.

The graph is constructed from harvesting and analyzing
blog post articles through a process separate from RedisGraph. The metadata
about the articles and the article text are stored in RedisGraph. Separately, an NER model is applied
to the content of the articles and the named entities extracted are also stored
in the graph in relation to the articles.

# Setup

The implementation is written in Python 3. To run the code, all you
will need to do is create a python environment and install the
required packages:

```
pip install -r requirements.txt
```

For a quick start, see the [project documentation](https://github.com/redis-developer/rediner)
and for more detailed information, see below.

## What you can do next {.tiles}

### Collecting Data {.tile}

See how articles are harvest and the NER model is applied. [More](collect.html)

### Data Architecture {.tile}

See how the graph is constructed. [More](data.html)

### Ingesting Data {.tile}

All about how to ingest articles and named entities into RedisGraph. [More](ingest.html)

### Querying Data {.tile}

Understand how to use Cypher to query the named entities and articles. [More](query.html)

### Demo Application {.tile}

Understand how to run the demo web application. [More](application.html)

### Serverless {.tile}

You can deploy the client application via serverless [More](serverless.html)
