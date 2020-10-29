---
title: Serverless Deployment
css: site.css
toc: false
---

The demo application can be deployed via AWS Lambda as a serverless
web application. The Redis database needs to be accessible from the VPC
in which the AWS Lambda function runs. Otherwise, the application remains
unchanged.

The Flask application is invoked via AWS Lambda using the
[flask-serverless](https://github.com/alexmilowski/flask-serverless) library.
The application must be packaged into a zip file containing all the
dependancies and the invocation function.

You can package the application by:

1. Configure your environment:

   ```
   export DOCKERID=yourdockerid
   export BASE=$HOME/workspace/github
   mkdir -p $BASE
   cd $BASE
   ```

   where the `yourdockerid` is your dockerhub identifier and `BASE`
   points to the directory where you want your code locally for the build.

1. If you haven't already done so, checkout the rediner project:

   ```
   git clone https://github.com/redis-developer/rediner.git
   ```

1. Checkout the flask-serverless project as a sibling directory:

   ```
   git clone https://github.com/alexmilowski/flask-serverless.git
   ```

   You should now have the `rediner` and `flask-serverless` as sibling directories.

1. The build script container image guarantees the deployment architecture matches for the
   packaged python packages. Build this image by:

   ```
   cd rediner/serverless
   docker build . -t $DOCKERID/rediner-demo-lambda-build
   ```

1. Build the packaging via the docker image:

   ```
   docker run --rm -v `pwd`:/build -v $BASE/rediner/:/rediner -v $BASE/flask-serverless/:/flask-serverless  $DOCKERID/rediner-demo-lambda-build:latest
   ```

After the container exits, you should have a `lambda.zip` to upload for the
AWS Lambda function.

To create the AWS Lambda function:

* Choose an Python 3.8 environment
* Select the appropriate VPC to enable access to your database
* Upload the `lambda.zip` as the implementation
* In "Basic Settings", change the handler to "production.lambda_handler" and
  adjust the timeout and memory (e.g., 2 minutes and 256MB)
* Set the GRAPH, REDIS_HOST, REDIS_PORT, and REDIS_PASSWORD environment variables
  to the appropriate values.

To expose the AWS Lambda function as a web application, you will will have to
configure an API Gateway and with a Lambda Proxy for the root resource "/"
and "/{proxy+}".
