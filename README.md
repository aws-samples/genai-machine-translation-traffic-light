# Traffic light based machine transalation review using generative AI LLM models

This repository contains a code sample that deploys an application that can perform the quality assessment of translated sentences from some common language pairs. The application takes a source sentence and it's translated counterpart and uses a Large Language Model to perform some quality assessment and provide a red, amber or green rating. The application will also render the LLM's reasoning as well as a list of errors it identifies. The intended use of this application is to assess the quality of machine translated models for common language pairs where a green rating needs no human intervention. A amber rating requires some corrections but the intent of the sentence is maintained in the translation. A red rating identifies poor quality translations that are not usable or change the meaning of the source sentence. 

This application is intended to showcase some of the interesting abilities of multi-lingual LLMs and is not intended to be a production ready system.

## Setup

To set up this project the following requirements are needed:

- Python 3.12
- AWS SAM CLI
- NPM

Create a python virtual environment first with `python3.12 -m venv .venv`

Next, activate the virtual environment and install the requirements:

```
source .venv/bin/activate
pip install -r requirements.txt
```

To build and deploy the application use the following two SAM CLI commands

```
sam build --template template.yaml
sam deploy --guided --profile <AWS_PROFILE>
```

This will first build the package for the application and create a `.aws-sam` folder locally.
The guided deploy will allow you to set and save parameters for future deployments.

# Configure UI

1. Open Cloudformation - goto "bedrock-traffic-light" stack and open the "Outputs" tab

2. Edit app/src/aws-exports file and replace the values of below config variables by referring to the output details from step 1 .

```bash
aws_appsync_graphqlEndpoint
aws_cognito_identity_pool_id
aws_user_files_s3_bucket
aws_user_pools_id
aws_user_pools_web_client_id
```

2. Create user in Amazon Cognito.

Open Amazon Cognito in AWS console and locate user pool created something like "UserPool-xxx". Under Users tab, select create user and follow the steps to setup your account for UI.

# Build UI package

To build the front end locally run:

```
cd ui
npm install
npm run build
```

Go to dist folder under ui folder and manually select all files and create a zip file. You can rename it as ui.zip

# Deploy App using AWS Amplify hosting

1. Login to AWS console and select AWS Amplify service
2. Select host web app in new app dropdown button
3. Choose "Deploy without git provider" under Amplify hosting and select continue button
4. Give name to you webapp, then upload ui.zip file or (select all files from dist folder if not zipped) from ui/dist folder and select "Save and deploy" button
5. Use the app url generated under domain field to launch it and follow the steps to login using user created in previous section.

# Clean up

To avoid incurring future charges, please clean up the resources created.

## Remove the stack

```
sam delete <stack name>
```

## Remove Amplify hosting

Open AWS Amplify in AWS console and select "delete app" action for your amplify hosting.
