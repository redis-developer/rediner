# rediner

Named Entity Recognition (NER) analysis in RedisGraph.

# Overview

This project contains an example of using the [SpaCy](https://spacy.io)
NER model to harvest
named entities from blog posts or other web pages. The crawler program
produces graph structures that can be loaded into RedisGraph for analysis
via Cypher Queries.

# Demo

A demo is available [online](http://rediner.milowski.io). Please be kind!

# A Quick Start

1. Create an environment an load the requirements:

   ```
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

1. Collect some entries:

   ```
   mkdir out
   python -m rediner.blog  --same --store --dir out --verbose https://www.milowski.com/
   ```

1. Run the SpaCy model:

   ```
   python -m rediner --yaml -r ner out > milowski-com-terms.yaml
   ```

1. Start RedisGraph:

   ```
   docker run -p 6379:6379 redislabs/redisgraph:latest
   ```

1. Setup the indexes:

   ```
   python demo/setupdb.py milowski.com
   ```

1. Ingest the data:

   ```
   python -m rediner load -r --graph milowski.com out
   python -m rediner load -r --graph milowski.com milowski-com-terms.yaml
   ```

1. Run the demo application:

   ```
   cd demo
   python view.py
   ```

1. View the application locally at http://localhost:5000/

Once the application is running, you can examine the dataset in various ways. For starters, try loading the graphs with the defaults by clicking on the 'Load'
button. This will load the entities that match the minimum counts and show a
graph of cooccurrences.

You can:

 * use the "same" checkbox to enable entities that co-occur on the same article.
 * use the "multiple" checkbox to enable entities that co-occur on more than one article.
 * use search to access the full text search. This will display a subgraph of
   entities from the search results.
 * clicking on a node in the graph will show the articles which contain the
   entities with a link back to the original resource.

# Next steps

You can view more extensive document on the [website](https://redis-developer.github.io/rediner/).
