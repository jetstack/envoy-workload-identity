from flask import Flask, render_template, request
import requests, os, json

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    project = os.environ["PROJECT_ID"]
    api_host = os.environ["API_HOST"]
    api_options = [{'display':'Storage buckets','option':'assets:storage.googleapis.com/Bucket'},{'display':'GKE Clusters','option':'assets:container.googleapis.com/Cluster'},{'display':'GKE Releases in europe-west1','option':'releases:europe-west1'},{'display':'GKE Releases in us-east4','option':'releases:us-east4'}]
    print(request)

    if request.method == 'POST':
        select_option = request.form.get("api_option")
        op = select_option.split(":")[1]
        if select_option.startswith("assets:"):
            api_path = f"assets?assetTypes={op}&contentType=RESOURCE"
        elif select_option.startswith("releases:"):
            api_path = f"locations/{op}/serverConfig"
        else:
            return render_template('index.html',api_options=api_options,response_text="Invalid selection")
        
        api_url = f'{api_host}/v1/projects/{project}/{api_path}'
        print(api_url)
        response = requests.get(api_url)
        
        json_fmt = json.dumps(json.loads(response.text), indent=2)
        
        return render_template('index.html',api_options=api_options,api_url=api_url,response_text=json_fmt)
    
    return render_template('index.html',api_options=api_options)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)