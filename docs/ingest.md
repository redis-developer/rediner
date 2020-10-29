---
title: Ingesting Data
css: site.css
toc: false
---

Ingesting data is a simple process that invokes the
[pypropgraph](https://github.com/alexmilowski/pypropgraph) library
to read the graph serializations and creates Cypher merge statements.

Assuming the blog posts are in a directory called "`out`", the articles
can be loaded into a local database via:

```
python -m rediner load -r --graph milowski.com out
```

And the named entities can also be loaded with the same command:

```
python -m rediner load -r --graph milowski.com milowski-com-terms.yaml
```

The `--graph` parameter specifies the RedisGraph key to be used.

The connection parameters to the database can be specified via parameters:

 * `--host host` - specifies the Redis host
 * `--port nnn` - specifies the Redis port
 * `--password auth` - specifies the Redis password

Or you can specify these with the environment variables `REDIS_HOST`, `REDIS_PORT`,
and `REDIS_PASSWORD`, respectively.
