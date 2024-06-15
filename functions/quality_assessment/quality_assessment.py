#Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#SPDX-License-Identifier: MIT-0

import json
import logging
import os

import boto3
from botocore.config import Config

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, CORSConfig
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext


tracer = Tracer()
logger = Logger()
cors_config = CORSConfig(allow_origin="*", allow_headers=["x-test"], max_age=300)
app = APIGatewayRestResolver(cors=cors_config)

BEDROCK_RUNTIME = boto3.client('bedrock-runtime')
DYNAMO_CLIENT = boto3.client('dynamodb')
TABLE_NAME = os.getenv("DDBTableName")


def get_call_body(system_prompt: str, 
                  messages: list[str], 
                  model_choice: str, 
                  temperature: float) -> tuple[str, dict]:
    
    """
    A helper function to construct the call body for the invoke

    :param system_prompt: System prompt to be passed to the LLM, retrieved from DynamoDB
    :param messages: A list of strings to be passed to the LLM as user messages
    :param model_choice: The model name to be used for the call
    :param temperature: Temperature setting to pass to the LLm
    :returns: A tuple object containing the model id and a dictionary of model kwargs
    :raises Exception: raises an exception if the model choice is invalid
    """

    logger.info("Getting call body")

    model_kwargs = {"prompt": ""}
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

    if model_choice == 'claude3':  
         logger.info("Generating Claude 3 args")
         model_kwargs = {
            "anthropic_version": "bedrock-2023-05-31",
            "temperature": temperature,
            "top_p": 1,
            "top_k": 250,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": messages
        }
         model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    elif model_choice == 'llama2':
        logger.info("Generating Llama 2 args")
        model_kwargs = {
            "prompt": system_prompt + str(messages),
            "temperature": temperature,
            "top_p": 1,
            "max_gen_len": 2048
        }
        model_id = "meta.llama2-70b-chat-v1"
    else:
        logger.error("Invalid model choice")
        raise Exception("Invalid model choice")
    
    return model_id, model_kwargs


def get_system_prompt(model_choice: str = 'claude', 
                      language: str = 'german') -> str:
    
    """
    A helper function to retrieve the system prompt from DynamoDB

    :param model_choice: The model name to be used for the invoke_model call
    :param language: The language of the prompt to be retrieved
    :returns: A string containing the full system prompt
    """
    
    logger.info("Selecting system prompt")

    prompt_id = "claude-sonnet"
    if model_choice == 'claude3':
        prompt_id = f"claude3-english-{language}"
    elif model_choice == 'llama2':
        prompt_id = f"llama2-english-{language}"

    logger.info(f"Retrieving Prompt ID: {prompt_id}")  # TODO: Exception handling required
    dynamo_item = DYNAMO_CLIENT.get_item(TableName=TABLE_NAME, Key={'prompt-id': {'S': prompt_id}})
    return dynamo_item["Item"]["prompt"]["S"]


def get_user_prompt(source: str, 
                    translation: str, 
                    language: str, 
                    model_choice: str) -> str:
    
    """
    A helper function to construct the user prompt for the ivoke_model call

    :param source: The source text to be translated
    :param translation: The translation text
    :param language: The language of the translation
    :param model_choice: The model name to be used for the call
    :returns: A string containing the full user prompt
    """

    logger.info("Constructing user prompt")
    prompt = f"""
                Rate the translation quality of the following translation:

                <english>{source}</english>
                <{language}>{translation}</{language}>

                Think step by step, identifying any issues with the translation and how that affects the rating.
                Output your rating assessment last.
            """
    if model_choice == "llama2-70b":  # Wrap Llama2 prompt into tags for model clarity
        prompt = "[INST]" + prompt + "\n[/INST]"
                    
    return prompt


def generate_message(bedrock_runtime: boto3.client, 
                     model_id: str, 
                     model_kwargs) -> str:

    """
    A function to call the bedrock-runtime service to generate a response from the chosen LLM

    :param bedrock_runtime: A boto3 client object for the bedrock-runtime service
    :param model_id: The official model id to be used for the call
    :param model_kwargs: A dictionary containing the various model arguements and settings
    :returns: A string containing the generated message
    """

    logger.info("Calling Bedrock.invoke_model")

    body=json.dumps(model_kwargs)

    response = bedrock_runtime.invoke_model(body=body, modelId=model_id)
    response_body = json.loads(response.get('body').read())
   
    return response_body


@app.post("/update-prompt")
@tracer.capture_method
def update_prompt() -> dict:
    print("Updating prompt")
    body = app.current_event.json_body
    print(body)
    try:
        prompt_id = body["promptView"]["label"]
        prompt_text = body["promptView"]["value"]

        DYNAMO_CLIENT.put_item(TableName=TABLE_NAME,
                                Item={
                                    'prompt-id': {'S': prompt_id},
                                    'prompt': {'S': prompt_text}
                                })

        return {"statusCode": 200}
    except Exception as e:
        logging.error(e)
        return {"statusCode": 500, 
                "body": e}

@app.get("/get-all-prompts")
@tracer.capture_method
def get_all_prompts() -> dict:

    """
    A function to retrieve the list of stored prompts from DynamoDB

    :returns: A list of dictionaries containing the prompt id and prompt text
    """

    logger.info(f"Retrieving prompt list from {TABLE_NAME}")

    prompts = DYNAMO_CLIENT.scan(TableName=TABLE_NAME)
    prompt_list = prompts["Items"]
    prompt_output_list = []
    for item in prompt_list:
        new_item = {"label": item["prompt-id"]["S"], "value": item["prompt"]["S"]}
        prompt_output_list.append(new_item)
    return {"prompts": prompt_output_list}


@app.post("/evaluate-translation")
@tracer.capture_method
def evaluate_translation() -> dict:
    print("Evaluating translation")
    body = app.current_event.json_body
    try:
        print(f"Event: {body}")
        # body = json.loads(translation_data)        
        source = body["source"]
        translation = body["translation"]
        language = body["language"]
        temperature = body["temperature"]
        llm_dict = body["llm"]
        llm = llm_dict["value"]

        system_prompt = get_system_prompt(llm, language)

        logger.info(f'Source: {source}')
        logger.info(f'Translation: {translation}')
        logger.info(f"LLM: {llm}")

        logger.info(f'System Prompt:\n{system_prompt}')

        user_message =  {"role": "user", "content": get_user_prompt(source, translation, language, llm)}
        messages = [user_message]

        model_id, model_kwargs = get_call_body(system_prompt, messages, llm, temperature)
        response = generate_message(BEDROCK_RUNTIME, model_id, model_kwargs)

        output = ""
        logger.info(f'Bedrock Full Response: {response}')
        if llm == 'claude3': 
            output = json.dumps(response['content'][0]["text"])
        elif llm == 'llama2':
            clean_gen = response['generation'][response['generation'].find("{"):(response['generation'].rfind("}")+1)]
            output = json.dumps(clean_gen)

        logging.info(f'Bedrock Response: {output}')
        return output

    except Exception as e:
        logging.error(e)
        return {"statusCode": 500,
                "body": e}


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext):
    logging.info(f"Event: {event}")
    return app.resolve(event, context)
