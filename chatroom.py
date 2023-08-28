from dotenv import load_dotenv
load_dotenv()
import openai
from typing import Dict, List
import os
import datetime as dt
import time
import json
import logging

#logging.basicConfig(level=logging.DEBUG)
#openai.api_base='http://localhost:8001/v1'

class Message:
    def __init__(self, message:str, name:str):
        self.name = name
        self.message = message
    name:str
    message:str
class ChatRoom:
    messages:List[Message] = []
def send_message_to_chatroom(message:str, chatroom:ChatRoom, username:str='anonymous'):
    chatroom.messages.append(Message(message, username))
def get_recent_messages_from_chatroom(chatroom:ChatRoom, count:int = 5):
    return  chatroom.messages[-count:]


class Character:
    def __init__(self, color:str, name:str, description:str):
        self.color=color
        self.description=description
        self.name=name
    color:str
    name:str
    description:str
    #personality = {'openness':0, 'conscientiousness':0, 'extraversion':0, 'agreeableness':0, 'neuroticism':0}

_json_shot = 'For example: If your name were Bob and you wanted to say "Hi There!" you would write {"name": "Bob", "message": "Hi There!"}'

def initialize_conversation(character:Character, topic=''):
    """This function creates a prompt that initializes the conversation"""
    task = f'Begin a conversation on {topic} in a brief chat message. {_json_shot}'
    instructions = f'You are playing the character of {character.name}.\n{character.description}'
    return instructions, task

def respond_prompt(character:Character):
    '''This function creates a prompt that responds to the previous response'''
    instructions = f'You are playing the character of {character.name}. \
    Move the conversation along in a fun way. \
    Never repeat a previous statement. \
    Reply in very brief chat messages, no more than a sentence or two. \
    Be funny and interesting. \
    If you have nothing interesting to say, say nothing. \
    {_json_shot}'
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

if __name__ == '__main__':
    
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    # create a folder to store the conversations if it does not exist
    path = 'ChatGPT_conversations'
    if not os.path.exists(path):
        os.makedirs(path)


    # initialize conversation on the following topic
    goal = 'open the door'
    conversation_rounds = 4
    chatroom = ChatRoom()
    agents:List[Character] = []

    color = 'brown'
    character = {
    "name": 'Smith',
    "description": 'You are a shrewd coach of a team. \
        You cannot play the game yourself. \
        You believe that evidence and reason are the only means to a good outcome. \
        Your role on the team is to coordinate and plan for your players. \
        You seek only to ensure that the team reaches their stated goal. \
        You try to steer the conversation back to the goal. \
        The game is safe for the players.'}
    agents.append(Character(color=color, name=character['name'], description=character['description']))

    color = 'pink'
    character = {
    "name": 'Jones',
    "description": 'You are a player in an escape room game. \
        You seek every means of helping the team to its goal. \
        You are careful that your statements are grounded in fact. \
        You can see a blue door. The floor is mostly covered in white tiles, except for one blue tile. \
        You cannot see the whole room. '}
    agents.append(Character(color=color, name=character['name'], description=character['description']))

    color = 'darkblue' 
    character = {
    "name": 'Penny',
    "description": 'You are a player in an escape room game. \
        You seek every means of helping the team to its goal. \
        You are careful that your statements are grounded in fact. \
        The floor is mostly covered in white tiles, except for one blue tile. \
        You cannot see the whole room. '}
    agents.append(Character(color=color, name=character['name'], description=character['description']))

    conversation = ''
    for round in range(conversation_rounds):
        for agent in agents:
            # initialize conversation
            text_color = agent.color
            name = agent.name
            if len(chatroom.messages) == 0:
                instructions, task = initialize_conversation(agent, goal)
                response = openai_request_initial(instructions, task)
            else:
                instructions = respond_prompt(agent)
                response = openai_request_continue(instructions, get_recent_messages_from_chatroom(chatroom))
            logging.debug(f'Response: {response}')
            try:
                j = json.loads(response)
                if j['message'].startswith('{') or j['message'].startswith('"'):
                    logging.error(f"Got a malformed message: {j['message']}")
                    continue
            except:
                logging.exception(f"Could not parse response: {response}")
                continue
            # wait some seconds 
            time.sleep(2)

            # add response to conversation after linebreak
            print(f'{name}: {response}')
            send_message_to_chatroom(message=j['message'], chatroom=chatroom, username=name)
            conversation += ' ' + f'<p style="color: {text_color};"><b>{name}</b>: {response}</p> \n'

            filename = f'{path}/GPTconversation_{timestamp}.html'
            with open(filename, 'w') as f:
                f.write(conversation)

