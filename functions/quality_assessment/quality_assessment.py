#Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#SPDX-License-Identifier: MIT-0

import json

import boto3
from botocore.config import Config

BEDROCK_RUNTIME = boto3.client('bedrock-runtime')
DYNAMO_CLIENT = boto3.client('dynamodb')
TABLE_NAME = "prompt-table"


def get_call_body(system_prompt, messages, model_choice='claude'):

    model_kwargs = {"prompt": ""}
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

    if model_choice == 'claude':  
         model_kwargs = {
            "anthropic_version": "bedrock-2023-05-31",
            "temperature": 0.0,
            "top_p": 1,
            "top_k": 250,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": messages
        }
         model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    elif model_choice == 'llama':
        model_kwargs = {
            "prompt": system_prompt + str(messages),
            "temperature": 0.0,
            "top_p": 0.9,
            "max_gen_len": 2048
        }
        model_id = "meta.llama2-70b-chat-v1"
        # model_id = "meta.llama3-8b-instruct-v1:0"
    else:
        raise Exception("Invalid model choice")
    
    return model_id, model_kwargs


def get_system_prompt(model_choice: str = 'claude', language: str = 'german') -> str:
    prompt_id = "claude-sonnet"
    if model_choice == 'claude':
        prompt_id = f"claude-sonnet-{language}"
    elif model_choice == 'llama':
        prompt_id = f"llama-70b-{language}"

    dynamo_item = DYNAMO_CLIENT.get_item(TableName=TABLE_NAME, Key={'prompt-id': {'S': prompt_id}})
    return dynamo_item["Item"]["prompt"]["S"]


def get_user_prompt(source: str, translation: str, language: str) -> str:

    prompt = f"""
                Rate the translation quality of the following translation:

                <english>{source}</english>
                <{language}>{translation}</{language}>

                Think step by step, identifying any issues with the translation and how that affects the rating.
                Output your rating assessment last.
               """
    return prompt


def generate_message(bedrock_runtime: boto3.client, model_id: str, model_kwargs) -> str:

    body=json.dumps(model_kwargs)

    response = bedrock_runtime.invoke_model(body=body, modelId=model_id)
    response_body = json.loads(response.get('body').read())
   
    return response_body


def get_prompt_list() -> list:
    prompts = DYNAMO_CLIENT.scan(TableName=TABLE_NAME)
    prompt_list = prompts["Items"]
    prompt_output_list = []
    for item in prompt_list:
        new_item = {"label": item["prompt-id"]["S"], "value": item["prompt"]["S"]}
        prompt_output_list.append(new_item)
    return prompt_output_list


def lambda_handler(event, context):
    try:
        print(type(event))
        print(f'Event: {event}')
        if event["body"] is None:
            print("Retrieving prompts...")
            prompt_output_list = get_prompt_list()

            print(f'Prompt List: {prompt_output_list}')
            return {"statusCode": 200,
                    "headers": {
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "*",
                        "Access-Control-Allow-Methods": "*",
                        "Content-Type": "application/json"
                    }, 
                    "body": json.dumps({"items": prompt_output_list})}
        
        model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'
        max_tokens = 4096
        body = json.loads(event["body"])
        source = body["source"]
        translation = body["translation"]
        language = body["language"]
        llm_dict = body["llm"]
        llm = llm_dict["value"]
        prompt_id = "claude-sonnet"

        system_prompt = get_system_prompt(prompt_id, language)

        print(f'Source: {source}')
        print(f'Translation: {translation}')
        print(f"LLM: {llm}")

        print(f'System Prompt:\n{system_prompt}')

        user_message =  {"role": "user", "content": get_user_prompt(source, translation, language)}
        messages = [user_message]

        print("Calling Bedrock...")
        model_id, model_kwargs = get_call_body(system_prompt, messages, llm)
        response = generate_message(BEDROCK_RUNTIME, model_id, model_kwargs)

        output = ""
        print(f'Bedrock Full Response: {response}')
        if llm == 'claude': 
            output = json.dumps(response['content'][0]["text"])
        elif llm == 'llama':
            output = json.dumps(response['generation'])

        # response = get_text_response(source, translation)
        print(f'Bedrock Response: {output}')
        return {"statusCode": 200, 
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Allow-Methods": "*",
                    "Content-Type": "application/json"
                },
                "body": output} 
                # "body": json.dumps(response['content'][0]["text"])}

    except Exception as e:
        print(e)
        return {"statusCode": 500, 
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Allow-Methods": "*",
                    "Content-Type": "application/json"
                },
                "body": e}
