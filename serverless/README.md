# Running on Serverless

The demo application can be run on AWS Lambda. This requires
building a packaging of the Flask application.

## Preparing the Build Script

The build script is a docker process that builds in the correct target
environment.

```
export DOCKERID=you
docker build . -t $DOCKERID/rediner-demo-lambda-build
```

## Building a distribution

The following will build a lambda.zip file for use on AWS Lambda

```
export BASE=$HOME/workspace/github
docker run --rm -v `pwd`:/build -v $BASE/rediner/:/rediner -v $BASE/flask-serverless/:/flask-serverless  $DOCKERID/rediner-demo-lambda-build:latest
```

You will need the supporting [flask-serverless](https://github.com/alexmilowski/flask-serverless) library cloned
locally and a sibling directory of this project.
