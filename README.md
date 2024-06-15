# Translation Quality Assessment Using LLMs

This repository contains a code sample to deploy an application that can perform quality assessment of translated sentences from some common language pairs. The application takes a source sentence and it's translated counterpart and uses a Large Language Model to perform some quality assessment and provide a RED, AMBER or GREEN rating. The application will also render the LLM's reasoning as well as a list of errors it identifies. 

The intended use of this application is to assess the quality of machine translated models for common language pairs where a GREEN rating needs no human intervention. An AMBER rating requires some corrections but the intent of the sentence is maintained in the translation. A RED rating identifies poor quality translations that are not usable or change the meaning of the source sentence. 

This application is intended to showcase some of the interesting abilities of multi-lingual LLMs and is not intended to be a production ready system.

## Setup

### Prerequisites

To deploy this application we need an AWS account with access to Bedrock specific Bedrock models. To enable the necessary models follow these steps:

1. Log in to the AWS Console for the account you will be using. 

1. Switch to the region that you want to deploy to. First check if [Bedrock is available in that region](https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-regions.html) and that the models you will be using are also available (Claude 3 Sonnet and Llama2 Chat 70B by default)

1. Navigate to Bedrock on the console and from the drop down menu go to `Model access`

1. Select `Modify model access` 

1. From the list of base models select:
    * Claude 3 Sonnet 
    * Llama Chat 70B

1. Check the terms and conditions of both models and that your usage will be within these.

1. Click `Next` Access should be granted immediately. If access is not granted within a few minutes, contact AWS Support.

#### Local Development and Build Requirements and Steps

- [Python 3.12](https://www.python.org/downloads/release/python-3120/)
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
- [NPM](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)

1. Create a python virtual environment first with `python3.12 -m venv .venv`

1. Next, activate the virtual environment and install the requirements:

    ```bash
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

1. Build the application using SAM CLI

    ```bash
    sam build --template template.yaml
    ```
    This will first build the package for the application and create a `.aws-sam` folder locally.

1. Deploy the built artifacts. For your first deployment use the `--guided` flag to answer a series of questions about the stack. These parameters can be saved locally and reused in future deployments.
    ```bash
    sam deploy --guided --profile <AWS_PROFILE>
    ```
    The first parameter requested will be the stack name. We will refer to this as `$STACK_NAME` in the rest of this document
    This will begin deploying the application to your specified AWS account. Deployment should take less than 15 minutes.
    When complete a set of outputs for the stack will be displayed, we wil use these in the next step to configure the UI.


### Configure UI

To configure the UI, we need to use some of the stack outputs.

1. Go to the console for the AWS account you deployed to and navigate to Cloudformation and then Stacks.

1. Locate the stack `$STACK_NAME`, open it and go to the Outputs tab.

1. Locally, open `ui/src/aws-exports.js` to edit the file.

1. Fill out the following values in `aws-exports.js` with the corresponding variables on the Outpts tab of Cloudformation Stacks:

    ```bash
    aws_project_region: $Region,
    aws_cognito_region: $Region,
    aws_user_files_s3_bucket_region: $Region,

    aws_user_files_s3_bucket: $S3Bucket,
    aws_cloud_logic_custom: [
        {
        name: "api",
        endpoint: "$Endpoint",
        },
    ],
    aws_user_pools_id: $UserPoolsId,
    aws_cognito_identity_pool_id: $IdentityPoolId,
    aws_user_pools_web_client_id: $UserPoolsWebClientId,
    ```

1. Next, we need to create a user in Amazon Cognito to access the application. Open Amazon Cognito in AWS console and locate user pool. It will be named `UserPool-$UserPoolsId`. Under Users tab, select create user and follow the steps to setup your account for UI access.

### Build UI Package

To build the front end locally run:

```bash
cd ui
npm install
```

You can then host the front end locally for demo purposes by using

```bash
npm run dev
```
This will provide a localhost url to access the application.

### Deploy App using AWS Amplify hosting

Go to dist folder under ui folder and manually select all files and create a zip file. You can rename it as ui.zip

1. Login to AWS console and navigate to AWS Amplify
1. Select `Create new app`
1. Choose `Deploy without Git` then Next
1. Go to your local repository and, from the `ui` folder, run:
    ```bash
    npm run build
    ```
    this will create a `ui/dist` folder.

1. Next, zip the dist folder
    ```bash
    cd dist
    zip -r $STACK_NAME *
    ```

1. Go back to the AWS Amplify console and upload your newly created zip file then hit `Save and deploy`

1. On success, a page will appear with a `Domain` link, click this and it will take you to your deployed application.

1. Use the user created in earlier steps to log in to the application.


## Clean up

To avoid incurring future charges, please clean up the resources created.

### Remove the stack

```bash
sam delete $STACK_NAME
```

### Remove Amplify hosting

Open AWS Amplify in AWS console and select "delete app" action for your amplify hosting.
