
function htmlescape(str) {
  return str.replace(/[&<>"'`=\/]/g, s => ({'&': '&amp;','<': '&lt;','>': '&gt;','"': '&quot;',"'": '&#39;','/': '&#x2F;','`': '&#x60;','=': '&#x3D;'})[s]);
}


class Viewer {
   constructor() {
      this.selected = null;
      this.textColor = "rgb(75,75,75)";
      this.backgroundColor = "rgb(221,160,221)";
      this.selectedColor = "rgb(148,0,211)";
      this.highlightColor = "rgb(255,89,0)";
      this.lineColor = "rgba(200,200,200,0.5)";
      this.borderColor = "rgb(100,100,100)";
      this.min_entity = 50;
      this.min_keyword = 1;
      this.node_scaling = 1;
      this.min_node_size = 20;
      this.show_debug = false;
   }
   init(element) {

      this.graph_element = element;

      $("#reload").click((e) => {
         this.load()
      });

      this.articles = document.getElementById("articles");
      this.articlesShown = true;

      this.results = document.getElementById("results");

      $("#min-keyword-range").change(() => {
         let value = $("#min-keyword-range").val();
         this.min_keyword = Number.parseInt(value);
         $("#min-keyword").val(value);
      });
      $("#min-keyword").change(() => {
         let value = $("#min-keyword").val();
         this.min_keyword= Number.parseInt(value);
         $("#min-keyword-range").val(value);
      });
      $("#min-entity-range").change(() => {
         let value = $("#min-entity-range").val();
         this.min = Number.parseInt(value);
         $("#min-entity").val(value);
      });
      $("#min-entity").change(() => {
         let value = $("#min-entity").val();
         this.min = Number.parseInt(value);
         $("#min-entity-range").val(value);
      });

      $("#dataset").change(() => {
         if (this.keywordGraph != null) {
            this.keywordGraph.destroy();
            this.keywordGraph = null;
         }
         $("#current").text('');
         $("#articles .term").empty();
         $("#articles .content").empty();
      });

      $("#search").on('keypress', (e) => {
         if (e.which==13) {
            this.search($("#search").val());
         }
      });
      $("#go-search").click((e) => {
         this.search($("#search").val());
      });

      fetch('/data/datasets').then( (response) => {
         return response.json();
      }).then( (datasets) => {
         let selected = true;
         for (let name of datasets) {
            $("#dataset").append(`<option value='${name}'${selected ? ' selected' : ''}>${name}</option>`);
            selected = false;
         }
      }).catch( (error) => {
         console.error('Cannot retrieve dataset list.',error)
      })


   }

   debug(msg) {
      if (this.show_debug) {
         console.log(msg)
      }
   }

   initGraph() {
      this.keywordGraph = cytoscape({
        container: $(this.graph_element),
        style: [
           {
               selector: "node",
               style: {
                 "label": "data(name)",
                 "width": "data(scaled_count)",
                 "height": "data(scaled_count)",
                 "background-color": this.backgroundColor,
                 "background-opacity": "0.75",
                 "font-size": "10px",
                 "font-weight": "bold",
                 "color" : this.textColor,
                 "border-color": this.borderColor,
                 "border-width": "1px"
               }
           },
           {
             selector: "edge",
             style: {
                "line-style" : "dashed",
                "line-dash-pattern" : [6,6],
                "line-color": this.lineColor,
                "width" : "1px"
             }
          }

        ]
      });
      this.keywordGraph.on('tap','node',(event) => {
         this.selectNode(event.target)
      })

   }

   load() {

      $("#articles .term").empty();
      $("#articles .content").empty();

      this.initGraph();

      this.min_keyword = Number.parseInt($("#min-keyword").val());
      this.min_entity = Number.parseInt($("#min-entity").val());
      this.words = {}
      this.word_count = 0;

      let dataset = $("#dataset").val();

      fetch(`/data/keywords?dataset=${dataset}`).then( (response) => {
         return response.json()
      }).then( (keywords) => {
         this.loadWords(keywords,'keyword',this.min_keyword)
         setTimeout(() => {
            fetch(`/data/entities?dataset=${dataset}`).then( (response) => {
               return response.json()
            }).then( (entities) => {
               this.loadWords(entities,'entity',this.min_entity)
               setTimeout(() => {
                  fetch(`/data/keywords/cooccurrences?dataset=${dataset}`).then( (response) => {
                     return response.json()
                  }).then( (cooccurrences) => {
                     this.loadCooccurrences(cooccurrences)
                     setTimeout(() => {
                        fetch(`/data/entities/cooccurrences?dataset=${dataset}`).then( (response) => {
                           return response.json()
                        }).then( (cooccurrences) => {
                           this.loadCooccurrences(cooccurrences)
                           setTimeout(() => {
                              this.layout()
                           },1)
                        }).catch( (error) => {
                           console.error('Cannot retrieve cooccurrences.',error)
                        })
                     },1);
                  }).catch( (error) => {
                     console.error('Cannot retrieve cooccurrences.',error)
                  })
               },1);
            }).catch( (error) => {
               console.error('Cannot retrieve cooccurrences.',error)
            })
         },1);
      }).catch( (error) => {
         console.error('Cannot retrieve keywords.',error)
      })

   }

   toggleArticles(flag) {
      this.articlesShown = flag;
      if (this.articlesShown) {
         $(this.articles).css("display","block");
      } else {
         $(this.articles).css("display","none");
      }
   }

   populateArticles(keyword) {
      let dataset = $("#dataset").val();
      fetch(`/data/articles?word=${encodeURIComponent(keyword)}&dataset=${dataset}`).then( (response) => {
         return response.json()
      }).then( (articles) => {
         $("#articles .term").empty();
         $("#articles .term").text(keyword)
         $("#articles .content").empty();
         articles.sort((x,y) => {
            if (y.datePublished==null) {
               return -1;
            }
            if (x.datePublished==null) {
               return 1;
            }
            return y.datePublished.localeCompare(x.datePublished);
         });
         for (let article of articles) {
            $("#articles .content").append(
               "<div class='article'>" +
               `<h4><a href="${htmlescape(article.url)}" target="article">${article.datePublished==null ? '' : article.datePublished.substring(0,article.datePublished.indexOf('T'))+' : '}${htmlescape(article.headline)}</a></h4>` +
               `<p>${article.description==null ? '' :article.description.substring(0,100) + ' ...'}</p>` +
               "</div>"

            )
         }
      }).catch( (error) => {
         console.error(`Cannot retrieve articles for keyword ${keyword}.`,error)
      })
   }

   selectNode(node) {
      if (this.selected!=null) {
         this.selected.style("background-color",this.backgroundColor);
         this.selected.connectedEdges().style("line-color",this.lineColor);
         this.selected.connectedEdges().style("line-style","dashed");
         this.selected.connectedEdges().style("width","1px")
         this.selected.connectedEdges().connectedNodes().forEach((e,index,collection) => {
            if (e==this.selected) {
               return;
            }
            e.style("background-color",this.backgroundColor);
         })
      }
      $("#articles .term").empty();
      $("#articles .content").empty();
      $("#current").empty();
      if (node==this.selected) {
         this.selected = null;
         return;
      }
      this.selected = node;
      this.selected.style("background-color",this.selectedColor);
      this.selected.connectedEdges().style("line-color",this.selectedColor);
      this.selected.connectedEdges().style("line-style","solid");
      this.selected.connectedEdges().style("width",1)
      this.selected.connectedEdges().connectedNodes().forEach((e,index,collection) => {
         if (e==this.selected) {
            return;
         }
         e.style("background-color",this.highlightColor);
      })
      $("#current").text(`${this.selected.data("name")} (${this.selected.data("type")},${this.selected.data("count")})`);
      setTimeout(() => {
         this.populateArticles(this.selected.data("name"));
      },1);
   }

   loadWords(words,type,minimum) {
      for (let word of words) {
         if (word.count<minimum) {
            this.debug(`Ignoring ${type} ${word.text} , count below ${minimum}`);
            continue;
         }
         console.log(`${word.text} : ${word.count}`)
         let data = this.words[word.text];
         if (data==null) {
            let id = `w${this.word_count}`
            data = {
               id: id,
               name: word.text,
               count: word.count,
               type: [type],
               scaled_count: this.min_node_size*Math.log(1+word.count*this.node_scaling)
            }
            this.words[word.text] = data;
            this.keywordGraph.add({ group: 'nodes', data: data })
            this.word_count += 1
         } else {
            data.count += word.count;
            data.type.push(type)
            this.keywordGraph.$(`#${data.id}`).data('scaled_count',this.min_node_size*Math.log(1+data.count*this.node_scaling));
         }
      }
   }

   loadCooccurrences(words) {
      for (let word of words) {
         let source = this.words[word.name];
         if (source==null) {
            continue;
         }
         //console.log(`${source} : ${keyword.index} -> ${keyword.occurs_with}`)
         for (let index of word.occurs_with) {
            if (word.index==index) {
               // Curated and non-curated can be the same keyword
               continue
            }
            let target = this.words[words[index].name];
            if (target!=null) {
               let edge_id = `e-${source.id}-${target.id}`;
               if (this.keywordGraph.$(`#${edge_id}`).length==0) {
                  //console.log(`edge from ${source.name}/${source.id} to ${target.name}/${target.id}`);
                  this.keywordGraph.add({ group: 'edges', data: { id: edge_id, source: source.id, target: target.id}})
               }
            }
         }
      }
   }

   layout() {
      this.keywordGraph.layout(
         { name: 'cose',
           animate: false,
           padding: 10,
           gravity: 0.10,
           idealEdgeLength: function( edge ){ return 1; },
           edgeElasticity: function( edge ){ return 4096; },
           nodeOverlap: 65335
        }
      ).run()
   }

   search(query) {
      console.log(`search: ${query}`);
      let dataset = $("#dataset").val();
      fetch(`/data/search?q=${encodeURIComponent(query)}&dataset=${dataset}`).then( (response) => {
         return response.json();
      }).then( (results) => {

         $("#articles .term").empty();
         $("#articles .content").empty();

         this.initGraph();
         this.words = {}
         this.word_count = 0;

         if (results.articles.length==0 && results.entities==0) {
            return;
         }

         this.loadWords(results.entities,'entity',1)

         setTimeout(() => {
            fetch(`/data/entities/cooccurrences?dataset=${dataset}`).then( (response) => {
               return response.json()
            }).then( (cooccurrences) => {
               this.loadCooccurrences(cooccurrences)
               setTimeout(() => {
                  this.layout()
               },1)
            }).catch( (error) => {
               console.error('Cannot retrieve cooccurrences.',error)
            })
         },1);

         $("#results .content").empty();
         results.articles.sort((x,y) => {
            if (y.datePublished==null) {
               return -1;
            }
            if (x.datePublished==null) {
               return 1;
            }
            return y.datePublished.localeCompare(x.datePublished);
         });
         for (let article of results.articles) {
            console.log(article);
            $("#results .content").append(
               "<div class='article'>" +
               `<h4><a href="${htmlescape(article.url)}" target="article">${article.datePublished==null ? '' : article.datePublished.substring(0,article.datePublished.indexOf('T'))+' : '}${htmlescape(article.headline)}</a></h4>` +
               `<p>${article.description==null ? '' :article.description.substring(0,100) + ' ...'}</p>` +
               "</div>"

            )
         }


      }).catch( (error) => {
         console.error(`Cannot search.`,error)
      })
   }
}
let app = new Viewer()


$(document).ready(function() {
   app.init("#graph")
})
