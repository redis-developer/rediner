---
title: Demo Application
css: site.css
toc: false
---

The demo application is build with [Flask](https://flask.palletsprojects.com/en/1.1.x/)
and you run it directly. All it needs is the connection parameters for the Redis database.

1. Start the web application:

   ```
   cd demo
   python view.py key ...
   ```

   The application defaults to a local database. You can connect to a
   Redis database with the following parameters:

    * --host ip

      The Redis host address
    * --port nnn

      The Redis port

    * --password password

      The Redis password

   The remaining arguments are the graph keys to use.

   Alternatively, all of the above settings can be set via environment variables
   or in the Flask configuration file (via the --config option).

   The environment variables are:

    * REDIS_HOST
    * REDIS_PORT
    * REDIS_PASSWORD
    * GRAPH

1. Visit http://localhost:5000/
