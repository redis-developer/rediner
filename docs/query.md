---
title: Querying Data
css: site.css
toc: false
---

## Cooccurrences of Named Entities

The main analysis that is shown in the demo application is the cooccurrences
of named entities:


* The named entities that cooccur in an article:

  ```
  MATCH (e1:NamedEntity)<-[:uses]-(a)-[:uses]->(e2:NamedEntity)
  WHERE e1 <> e2 AND e1.text < e1.text
  RETURN e1.text, e2.text
  ```

* The named entities that cooccur on two different articles:

  ```
  MATCH (a1)-[:uses]->(e1:NamedEntity)<-[:uses]-(a2)-[:uses]->(e2:NamedEntity)<-[:uses]-(a1)
  WHERE a1 <> a2 and e1 <> e2 AND e1.text < e2.text
  RETURN e1.text, e1.text
  ```

* The named entities that occur on more than one article:

  ```
  MATCH (a)-[u:uses]->(e:NamedEntity)
  WITH e, count(a) AS refs, sum(u.count) AS total
  WHERE refs>1
  RETURN e.text, refs, total
  ```

* The name entities that occur on at least two different articles:

  ```
  MATCH (a1)-[:uses]->(e:NamedEntity)<-[:uses]-(a2)
  WHERE a1 <> a2 AND a1.headline < a2.headline
  RETURN e.text, count(a1)
  ```

## Search

We can also search articles:

```
CALL db.idx.fulltext.queryNodes('BlogPosting', '{query}') YIELD node
RETURN node.url, node.headline, node.datePublished, node.description
```

and find their related named entities:

```
CALL db.idx.fulltext.queryNodes('BlogPosting', '{query}') YIELD node
MATCH (node)-[u:uses]->(e:NamedEntity)
RETURN e.text, count(node), sum(u.count)
```
