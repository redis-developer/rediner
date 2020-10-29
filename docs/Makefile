PAGES=../../gh-pages
PROJECT=rediner
TARGETDIR=$(PAGES)/$(PROJECT)
PANDOC=pandoc
PANDOC_OPTIONS=--toc -s --section-divs --include-in-header=header.html --include-before=site.html

$(TARGETDIR)/%.css: %.css
	cp $< $@

$(TARGETDIR)/%.svg: %.svg
	cp $< $@

$(TARGETDIR)/%.png: %.png
	cp $< $@

$(TARGETDIR)/%.js: %.js
	cp $< $@

$(TARGETDIR)/%.html: %.md header.html site.html
	$(PANDOC) $(PANDOC_OPTIONS) -f markdown -t html5 -o $@ $<


CSS=\
$(TARGETDIR)/base.css \
$(TARGETDIR)/site.css

DOCS=\
$(TARGETDIR)/index.html \
$(TARGETDIR)/collect.html \
$(TARGETDIR)/data.html \
$(TARGETDIR)/ingest.html \
$(TARGETDIR)/query.html \
$(TARGETDIR)/application.html \
$(TARGETDIR)/serverless.html

RESOURCES=\
$(TARGETDIR)/site.js \
$(TARGETDIR)/ner-graph.png


all: $(CSS) $(DOCS) $(RESOURCES)

clean.html:
	rm -f $(DOCS)
