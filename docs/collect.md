---
title: Collecting Data
css: site.css
toc: false
---

Blogs are articles that are typically published with a certain minimum amount
of metadata like the date published, title, author, keywords, etc. Modern
blog posts are often encoded with [schema.org](https://schema.org/) annotations (see [BlogPosting](https://schema.org/BlogPosting))
as well as other metadata facets encoded in various ways. As such, within the
raw HTML for the blog article web page there is both metadata and the
article body that can be extracted with a modicum of effort.

## Crawling Blog Articles

A simple crawler can be invoked to visit each blog article web page. The
crawler assumes the blog is structure in one of two ways:

1. An index page that has a collection of links to each blog page. These index
   pages can be paginated with next/previous links.

2. A starting blog page links to the "previous" entry in the blog.

The crawler can be invoked by:

```
python -m rediner.blog url ...
```

From the starting URLs the crawler will inspect the page for articles. If the
`--same` option is specified, it will assume the blog is structured via method
(2) above. Otherwise, the blog is assumed to be structured with index pages and
separate blog article pages.

The defaults are structured to rebuild the datasets for the blogs shown
in the demo. That is, the crawler knows how to traverse and extract the
articles from:

 * [`https://www.milowski.com/`](https://www.milowski.com/)
 * [`https://redislabs.com/company-blog/`](https://redislabs.com/company-blog/)
 * [`https://redislabs.com/tech-blog/`](https://redislabs.com/tech-blog/)

To run the crawler on other blogs or adjust how the output is handled, the following
options may be useful:

 * `--verbose` - Indicates that the process should be verbose and output status
   and debugging information.
 * `--entry` - a CSS selector to use to find an entry link (multiple allowed)
 * `--next` - a CSS selector to use to find the next page (i.e., either the next index page or next blog post) (multiple allowed)
 * `--url-only` - Output only the URLs of the blog article pages
 * `--same` - Indicates that the index and blog article are on the same page (i.e., method 2 above)
 * `--entry-container` - a CSS selector to find the article body on the page (multiple allowed)
 * `--remove` - a CSS selector of content to ignore for text extraction (multiple allowed)
 * `--full-types` - use fully qualified type labels in the output
 * `--store` - store the output in separate files
 * `--extension` - the output file extension to use.
 * `--stub` - the stub for the generated filename.
 * `--dir` - the directory in which to store the output files

For example, the explicit parameters for `https://www.milowski.com/`
are:

```
python -m rediner.blog --store --dir out \
--entry "article[typeof]" \
--next "header .article-navigation a[title='preceding entry']" \
--remove pre --remove code \
--entry-container "article[resource]" \
https://www.milowski.com/
```

## Extracting Named Entities

The SpaCy NER model can be applied to the harvested data to produce a
serialization of the entities to be added to the graph:

```
python -m rediner --yaml -r ner out > milowski-com-terms.yaml
```

The output file will contain the name entity nodes and the edges from the
article node to the named entity (the `uses` relation).

## Other Web Pages

The same technique can be use on other web pages without too much effort. The
`harvest_entry` function in `rediner.blog` can be applied to any page
to generate an entry. Since random web pages are less regular in how
the link to each other, the crawler will have to determine the set of
URLs for any website that will be crawled. One simple way to do this is
to predetermine the set of URLs to crawl, places them on the command line, and
then use the `--same` option to extract the article.
