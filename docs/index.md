---
title: Rediner - Named Entity Analysis in RedisGraph
css: site.css
toc: false
---

This project provides a demonstration of the use of the [RedidGraph](https://oss.redislabs.com/redisgraph/) to
store and analyze named entities (people, places, objects, etc.). The
data collection involves a
[Named Entity Recognition](https://en.wikipedia.org/wiki/Named-entity_recognition) (NER)
model from [SpaCy](https://spacy.io).

The example application uses Flask and allows you to analyze blog posts and navigate the
articles via the cooccurences of name entities. The architecture is a simple
two-tier application where the web application uses Cypher to directly query
RedisGraph.

The graph in the database is constructed from the harvesting and analysis of
the blog post articles throw a separate process. The metadata about the articles
and the article contents are stored in RedisGraph. A NER model is applied
to the content of the articles and those named entities extracted are stored
in the graph in relation to the articles.

# Setup

All the implementation is written in Python 3. To run the code, all you
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

You can deploy the client application via serverless (e.g. AWS Lambda) [More](serverless.html)
