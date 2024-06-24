# envoy-workload-identity

This repo contains demo/PoC scripts for showing how to use Envoy Proxy to inject a valid Authorization header into a GCP API call. There are 2 demos:

1. In [local-dev](./local-dev/) Docker Compose is used to start Envoy Proxy and mock GCP Metadata servers. Curl will be used to demo calling the GCP Asset Inventory API.

1. In [cloud-run](./cloud-run) GCP's Cloud Run service is used to host a simple Python web app (see [./api-client](./api-client)) with Envoy Proxy as a sidecar. There is no need for a mock Metadata service as the 'real' GCP Metadata service is available to Cloud Run service.

## Local demo

This uses Docker Compose to run Envoy Proxy and a mock GCP metadata server to show how Envoy is used to get an auth token from the Metadata service and inject it as an Authorization header in the API request before its sent to the API endpoint.

### Pre-requisites

A GCP Project and Service Account with IAM permissions for calling the GCP Asset Inventory API (Cloud Asset Viewer role).  
Download the SA json key and store.  
Ensure the GCP Asset Inventory API is enabled for this Project.  

The custom Envoy Proxy image has already been built and is stored in an accessable registry (see [this readme](./envoyproxy/README.md)).

### Running

Export the following env vars:

- PROJECT_ID=GCP Project ID
- SA_KEY_PATH=absolute path to the SA key.json file
- SA_EMAIL=the SA's email, e.g. something@myproject.iam.gserviceaccount.com
- ENVOY_IMAGE=url of the Envoy Docker image you built

Generate the config files:

```bash
cd ./local-dev
envsubst < compose.yaml.tmpl > compose.yaml
envsubst < metadata-config.json.tmpl > config.json
```

Login to the Docker registry (if not public):

GCP example (<https://cloud.google.com/artifact-registry/docs/docker/authentication>):

```bash
gcloud auth login
gcloud auth configure-docker us-west1-docker.pkg.dev,europe-west1-docker.pkg.dev
```

And start Docker Compose:

```bash
docker compose up
```

Now use curl to query the Asset Inventory API:

```bash
curl -vvv "localhost:10000/v1/projects/$PROJECT_ID/assets?assetTypes=storage.googleapis.com/Bucket&contentType=RESOURCE"
```

You should see a json response containing details of all the storage buckets in the project. Logging from the Envoy container is deliberately verbose - this can be removed by editing `local-envoy-demo.yaml` and removing the logging lines from the inline Lua script.

## Cloud Run demo

### Pre-requisites

A GCP Project and Service Account with IAM permissions for calling the GCP Asset Inventory API (Cloud Asset Viewer role).  
Ensure the GCP Asset Inventory and Cloud Run Admin APIs are enabled for this Project.  

The custom Envoy Proxy image has already been built and is stored in an accessable registry (see [this readme](./envoyproxy/README.md)).

The Python api-client app has been dockerised and the image stored in an accessable registry (see [this readme](./api-client/README.md)).

### Running

Export the following env vars:

- PROJECT_ID = GCP Project ID
- SA_KEY_PATH = absolute path to the SA key.json file
- SA_EMAIL = the SA's email, e.g. something@myproject.iam.gserviceaccount.com
- ENVOY_IMAGE = url of the Envoy Docker image you built
- ENVOY_CONFIG_BUCKET = the name of a storage bucket for storing the Envoy Proxy config

Generate the Cloud Run service config:

```bash
cd ./cloud-run
envsubst < service.yaml.tmpl > service.yaml
```

Create the bucket for the Envoy config and upload `cloudrun-envoy-demo.yaml` into it:

```bash
gcloud storage buckets create gs://$ENVOY_CONFIG_BUCKET --location=europe-west1 --project=$PROJECT_ID
gcloud storage cp ./cloudrun-envoy-demo.yaml gs://$ENVOY_CONFIG_BUCKET
```

Deploy the Cloud Run service and make it publically accessable over the Internet.

```bash
gcloud run services replace service.yaml --region=europe-west1 --project=$PROJECT_ID
gcloud run services set-iam-policy envoy-proxy-demo public-access-policy.yaml --region=europe-west1 --project=$PROJECT_ID
```

NOTE: be aware that there is no authentication configured on the Cloud Run URL, so the demo Python app is accessible anonymously over the public Internet.

To confirm the service is running and retrieve its URL:

```bash
gcloud run services describe envoy-proxy-demo --region=europe-west1 --project=$PROJECT_ID
```

Load the URL in a browser page and select an option from the drop-down and click Submit. The Python code running in Cloud Run will forward the request on to the Envoy Proxy sidecar which will call the Metadata service to get a valid token and then inject the token.
