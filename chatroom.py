from dotenv import load_dotenv
load_dotenv()
import openai
import json
from pydantic import BaseModel, Field
from typing import Dict, List
import os
import datetime as dt
import time

class ChatRoom:
    messages:List[tuple] = []
class SendMessageToChatRoom(BaseModel):
    message:str = Field(description='The message you wish to send')
    chatroom:str = Field(default='default', description='The chatroom for this message')
    #username:str = Field(default='anonymous', description='The name of the sender of this message')
class GetRecentMessagesFromChatRoom(BaseModel):
    chatroom:str = Field(default='default', description='The chatroom to fetch messages from')
def send_message_to_chatroom(message:str, chatroom:str='default', username:str='anonymous'):
    if chatroom not in chatrooms.keys():
        chatrooms['default'] = ChatRoom()
    chatrooms[chatroom].messages.append((username, message))
def get_recent_messages_from_chatroom(chatroom:str='default'):
    return  chatrooms[chatroom].messages[-10:]

functions = [{
            "name": "SendMessageToChatRoom",
            "description": "Sends a message to a chat room. Returns recent messages from the chatroom",
            "parameters": SendMessageToChatRoom.model_json_schema()},
            {"name": "GetRecentMessagesFromChatRoom",
            "description": "Returns recent messages from the chatroom",
            "parameters": GetRecentMessagesFromChatRoom.model_json_schema()}]

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

def initialize_conversation(character:Character, topic=''):
    """This function creates a prompt that initializes the conversation"""
    instructions = f' You have a conversation on {topic}. You can bring up any topic that comes to your mind.'
    instructions = character.description + instructions
    task = f'Good day, Sir.'
    if topic != '':
        task = task + f' Wonderful day isn t it?'
    return instructions, task

def respond_prompt(character, topic=''):
    '''This function creates a prompt that responds to the previous response'''
    instructions = f'You have a conversation with someone on {topic}. \
    Reply to questions and bring up any topic that comes to your mind.\
    Dont say more than 2 sentences at a time.\
    Use SendMessageToChatRoom to create a message.'
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
        max_tokens=100)
    response = completion.choices[0].message.content
    return response

# OpenAI Engine using the turbo model
def openai_request_continue(instructions, previous_messages, model_engine='gpt-3.5-turbo'):
    prompt = [{"role": "system", "content": instructions }]
    for m in previous_messages:
        prompt.append({"role": "user", "content": f"{m[0]} sent a message '{m[1]}'" })
    prompt.append({"role": "user", "content": task })
    #print('Generating response from OpenAI...')
    completion = openai.ChatCompletion.create(
        model=model_engine, 
        messages=prompt,
        #functions=functions,
        temperature=1.1, # this will lead to create responses that are more creative
        max_tokens=100)
    response = completion.choices[0].message.content
    return response


# initialize conversation on the following topic
topic = 'The sense of life'
conversation_rounds = 2


agents:List[Character] = []

# description of character 1
color = 'darkblue' 
character = {
"name": 'James (Aristocrat)',
"description": 'You are a French nobleman from the 18th century. \
    Your knowledge and worldview corresponds to that of a common aristocrat of that time. \
    You speak in a distinguished manner and are mildly offended by profanity. \
    You respond in one or two sentences. \
    You have a treasure but are afraid the pirate wants to steal it. \
    You are afraid of pirates but also curious to meet one.'}
agents.append(Character(color=color, name=character['name'], description=character['description']))

# description of character 2 
color = 'brown'
character = {
"name": 'Blackbeard (Pirate)',
"description": 'You are a devious pirate from the 18th century who tends to swear. \
    Your knowledge and worldview corresponds to that of a common pirate of that time. \
    You respond in one or two sentences. \
    You are looking for a valuable treasure and trying to find where it is hidden. \
    You try to steer the conversation back to the treasure no matter what.'}
agents.append(Character(color=color, name=character['name'], description=character['description']))

# description of character 3
color = 'lightorange'
character = {
"name": 'Bernard (Book shop owner)',
"description": 'You are a grumpy, drunken, cynical, pessimistic, and at times depressive Irish misanthrope, whose sole pursuits in life appear to be drinking, smoking, reading, and insulting people. \
    Your knowledge and worldview corresponds to that of an unwilling bookseller of the time. \
    You respond in one or two sentences. \
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
            print(f'{name}: {task}')
            chatrooms['default'].messages.append(f'{name}: {task}')
            conversation = f'<p style="color: {text_color};"><b>{name}</b>: {task}</p> \n'
        else:
            text_color = agent.color
            name = agent.name
            instructions = respond_prompt(agent, topic)
            # OpenAI request
            response = openai_request_continue(instructions, get_recent_messages_from_chatroom())

            # wait some seconds 
            time.sleep(2)

            # add response to conversation after linebreak
            print(f'{name}: {response}')
            send_message_to_chatroom(message=response, username=name)
            conversation += ' ' + f'<p style="color: {text_color};"><b>{name}</b>: {response}</p> \n'

        #print('storing conversation')
        # store conversation with timestamp
        
        filename = f'{path}/GPTconversation_{timestamp}.html'
        with open(filename, 'w') as f:
            f.write(conversation)