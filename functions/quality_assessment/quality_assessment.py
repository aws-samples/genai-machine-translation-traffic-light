import json
import logging
import os

import boto3
from botocore.config import Config


logger = logging.getLogger()
logger.setLevel(os.getenv("LogLevel", logging.INFO))

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


def get_prompt_list() -> list[dict]:

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
    return prompt_output_list


def lambda_handler(event, context) -> dict:

    """
    The lambda handler function for the quality assessment lambda function

    :param event: A dictionary containing the event data
    :param context: A dictionary containing the context data
    
    :returns: A dictionary containing the response data
    """

    try:
        logging.info(f"Event: {event}")
        if event["body"] is None:
            prompt_output_list = get_prompt_list()

            logger.info(f'Prompt List: {prompt_output_list}')
            return {"statusCode": 200,  # TODO: Error handling
                    "headers": {
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "*",
                        "Access-Control-Allow-Methods": "*",
                        "Content-Type": "application/json"
                    }, 
                    "body": json.dumps({"items": prompt_output_list})}
        
        model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'
        body = json.loads(event["body"])
        source = body["source"]
        translation = body["translation"]
        language = body["language"]
        temperature = body["temperature"]  # TODO: Currently not passed by app...
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

        print(f'Bedrock Response: {output}')
        return {"statusCode": 200, 
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Allow-Methods": "*",
                    "Content-Type": "application/json"
                },
                "body": output} 

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
