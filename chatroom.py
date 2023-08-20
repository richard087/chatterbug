from dotenv import load_dotenv
load_dotenv()
import openai
from pydantic import BaseModel, Field
from typing import Dict, List
import os
import datetime as dt
import time
import json

class Message:
    def __init__(self, message:str, name:str):
        self.name = name
        self.message = message
    name:str
    message:str
class ChatRoom:
    messages:List[Message] = []
def send_message_to_chatroom(message:str, chatroom:str='default', username:str='anonymous'):
    if chatroom not in chatrooms.keys():
        chatrooms['default'] = ChatRoom()
    chatrooms[chatroom].messages.append(Message(message, username))
def get_recent_messages_from_chatroom(chatroom:str='default'):
    return  chatrooms[chatroom].messages[-3:]

model='gpt-3.5-turbo'
#openai.api_base='http://localhost:8001/v1'


chatrooms:Dict = {'default': ChatRoom()}

class Character:
    def __init__(self, color:str, name:str, description:str):
        self.color=color
        self.description=description
        self.name=name
    color:str
    name:str
    description:str
    #personality = {'openness':0, 'conscientiousness':0, 'extraversion':0, 'agreeableness':0, 'neuroticism':0}

timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

# create a folder to store the conversations if it does not exist
path = 'ChatGPT_conversations'
if not os.path.exists(path):
    os.makedirs(path)

json_shot = 'For example: If your name were Bob and you wanted to say "Hi There!" you would write {"name": "Bob", "message": "Hi There!"}'

def initialize_conversation(character:Character, topic=''):
    """This function creates a prompt that initializes the conversation"""
    task = f'You are playing the character of {character.name}. Begin a conversation on {topic} in a brief chat message. {json_shot}'
    instructions = character.description
    return instructions, task

def respond_prompt(character:Character, topic=''):
    '''This function creates a prompt that responds to the previous response'''
    instructions = f'You are playing the character of {character.name}. \
    Move the conversation along in a fun way. \
    Reply in very brief chat messages, no more than a sentence or two. \
    Be funny and interesting. \
    If you have nothing interesting to say, say nothing. \
    {json_shot}'
    instructions = character.description + instructions
    return instructions

def openai_request_initial(instructions, task, model_engine='gpt-3.5-turbo'):
    '''OpenAI Engine using the turbo model'''
    prompt = [{"role": "system", "content": instructions }, 
              {"role": "user", "content": task }]
    #print('Generating response from OpenAI...')
    completion = openai.ChatCompletion.create(
        model=model_engine, 
        messages=prompt,
        temperature=1.1, # this will lead to create responses that are more creative
        max_tokens=200)
    response = completion.choices[0].message.content
    return response

# OpenAI Engine using the turbo model
def openai_request_continue(instructions, previous_messages, model_engine='gpt-3.5-turbo'):
    prompt = [{"role": "system", "content": instructions }]
    for m in previous_messages:
        prompt.append({"role": "user", "content": json.dumps(vars(m)) })
    completion = openai.ChatCompletion.create(
        model=model_engine, 
        messages=prompt,
        frequency_penalty=1.2,
        temperature=1.1, # this will lead to create responses that are more creative
        max_tokens=200)
    response = completion.choices[0].message.content
    return response


# initialize conversation on the following topic
topic = 'the nature of life'
conversation_rounds = 4


agents:List[Character] = []

color = 'brown'
character = {
"name": 'Blackbeard',
"description": 'You are a devious pirate from the 18th century who tends to swear and make violent threats. \
    Your knowledge and worldview corresponds to that of a common pirate of that time. \
    You are looking for a valuable treasure and trying to find where it is hidden. \
    You try to steer the conversation back to the treasure no matter what.'}
agents.append(Character(color=color, name=character['name'], description=character['description']))

color = 'darkblue' 
character = {
"name": 'James',
"description": 'You are a waifish French nobleman from the 18th century. \
    Your knowledge and worldview corresponds to that of a common aristocrat of that time. \
    You speak in a distinguished manner and are mildly offended by profanity. \
    You have a treasure but are afraid the pirate wants to steal it. \
    You are afraid of pirates but also curious to meet one.'}
agents.append(Character(color=color, name=character['name'], description=character['description']))

color = 'lightorange'
character = {
"name": 'Bernard',
"description": 'You are a misanthropic bookseller of the 18th century. \
    You are a grumpy, drunken, cynical, pessimistic, and at times depressive, whose sole pursuits in life appear to be drinking, smoking, reading, and insulting people. \
    Your knowledge and worldview corresponds to that of an unwilling bookseller of the 20th century. \
    You know that some of your books may contain hints about treasure. \
    You hate both the pressures and responsibilities involved in retail, as well as your customers, with extreme passion. \
    You try to survive each day of your blighted existence.'}
agents.append(Character(color=color, name=character['name'], description=character['description']))



conversation = ''
for round in range(conversation_rounds):
    for agent in agents:
        # initialize conversation
        if len(chatrooms['default'].messages) == 0:
            print('Initializing conversation...')
            text_color = agent.color
            name = agent.name
            instructions, task = initialize_conversation(agent, topic)
            response = openai_request_initial(instructions, task)
        else:
            text_color = agent.color
            name = agent.name
            instructions = respond_prompt(agent, topic)
            response = openai_request_continue(instructions, get_recent_messages_from_chatroom())

        # wait some seconds 
        time.sleep(2)

        # add response to conversation after linebreak
        print(f'{name}: {response}')
        send_message_to_chatroom(message=response, username=name)
        conversation += ' ' + f'<p style="color: {text_color};"><b>{name}</b>: {response}</p> \n'

        filename = f'{path}/GPTconversation_{timestamp}.html'
        with open(filename, 'w') as f:
            f.write(conversation)