For building the custom image for the demo Python app.

## Usage
`export PROJECT_ID=my_project`

Create repository in Artifact Registry:  
`gcloud artifacts repositories create envoy-demo --repository-format=docker --location=europe-west1 --description="Images for use with Envoy demo" --project=$PROJECT_ID`

Use Cloud Build to build the image and push it into Artifact Registry:
```
gcloud builds submit --region=europe-west1 --config cloudbuild.yaml --project=$PROJECT_ID
```