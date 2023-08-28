from dotenv import load_dotenv
load_dotenv()
import openai
import json
import logging
from gridworld import Grid
from chatroom import Message, ChatRoom, send_message_to_chatroom, get_recent_messages_from_chatroom
from typing import List, Dict, Any, AnyStr

logger = logging.basicConfig(level=logging.DEBUG)

chatrooms:Dict = {'default': ChatRoom()} #TODO make this not terrible



#openai.debug=True
#openai.api_base='http://localhost:8001/v1'

def init_game() -> Grid:
    g = Grid(height=3, width=2)
    g.add_object((0, 0), g.Door(colour='blue'))
    g.set_tile_colour((0, 2), 'blue')
    return g



def get_view_for_player(g: Grid, p:Grid.Player = None) ->str:
    system = f'You are a helpful assistant. You must only act on the data presented to you. \
        You are observing a game board. please give a brief summary of the state of game. \
        The board is made up of tiles, each of which has a colour and may contain an object. \
        Describe any tile with an unusual colour and where it is. \
        Describe each object (player, door, etc.) and where it is relative to the player {p.name}. \
        Describe relative position using cardinal directions (North, East, South, West). \
        Coordinates ( 0, 0 ) are the north-west corner and (maximum , maximum) are the south-east corner.'
    prompt = [{"role": "system", "content": system }, 
                {"role": "user", "content": g.to_json() }]
    completion = openai.ChatCompletion.create(
            model='gpt-3.5-turbo', 
            messages=prompt,
            max_tokens=300)
    response = completion.choices[0].message.content
    return response

def propose_action_for_player(current_view:str, p:Grid.Player, previous_messages:List[Message] = []) ->str:
    system = f'You are player "{p.name}". You are in an escape room game. You must only act on the data presented to you. \
        You seek every means of helping the team to its goal. \
        You are careful that your statements are grounded in fact.'
    prompt = [
        {"role": "system", "content": system },
        {"role": "user", "content": rules },
        {"role": "user", "content": f'The current state of the game follows\n{current_view}' },
        {"role": "user", "content": f'Propose what to do to achieve the goal.' },
        ]
    for m in previous_messages:
        if m.name ==p.name:
            prompt.append({"role": "assistant", "content": m.message })
        else:
            prompt.append({"role": "user", "content": m.message })
    completion = openai.ChatCompletion.create(
            model='gpt-3.5-turbo', 
            messages=prompt,
            max_tokens=300)
    response = completion.choices[0].message.content
    return response

def return_critique(approved:bool, critique:str = ''): # should never be called
    logging.error(f'return_critique called with approved: {approved} and critique: {critique}')
    assert False

def move_player(direction:str, g:Grid, player:Grid.Player):
    l = g.where_is(player)[0] # should not have duplicates
    if direction == "north":
        t = (l[0], l[1] + 1)
    elif direction == "south":
        t = (l[0], l[1] - 1)
    elif direction == "east":
        t = (l[0] + 1, l[1])
    elif direction == "west":
        t = (l[0] - 1, l[1])
    else:
        raise Exception(f'direction argument does not have an allowable value. Received {direction}')
    g.move_object(l, t)

gpt_function_interfaces = [
    {
        "name": "return_critique",
        "description": "Return a structured response for a player proposal",
        "parameters": {
            "type": "object",
            "properties": {
                "approved": {
                    "type": "boolean",
                    "description": "'true' indicates that the player proposal should be acted upon",
                },
                "critique": {"type": "string", "description": "A brief explanation of why the player proposal has been approved or not."},
            },
            "required": ["approved", "critique"],
        }
    },
    {
        "name": "move_player",
        "description": "Move the player to a tile without an object (player or door)",
        "parameters": {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum":["north", "east", "south", "west"],
                    "description": "The direction to move the player. Starting at ( 0 , 0 ): 'north' would move to ( 0 , 1 ); 'east' would move to ( 1 , 0 ); 'south' would move to ( 0 , -1 ); 'west' would move to ( 0 , -1 ).",
                },
            },
            "required": ["direction"],
        }
    }
]
def critique_action(current_view:str, p:Grid.Player, proposal:str) ->str:
    system = f'You are the coach of a team. You can only advise the players, you have no other influence on the game. You must only act on the data presented to you.'
    prompt = [{"role": "system", "content": system }, 
                {"role": "user", "content": rules },
                {"role": "user", "content": f'The current state of the games follows\n{current_view}' },
                {"role": "user", "content": f"Player {p.name} has made the proposal below. Examine the players proposal and consider whether it is allowable in the game and whether it is helpful to the team. State explicitly, whether you approve of a player proposal or briefly state what is wrong with the proposal." },
                {"role": "user", "content": proposal },]
    completion = openai.ChatCompletion.create(
            model='gpt-3.5-turbo', 
            messages=prompt,
            functions=gpt_function_interfaces,
            function_call={"name": "return_critique"},
            max_tokens=300)
    response_message = completion["choices"][0]["message"]
    assert response_message.get("function_call")
    return response_message

def translate_intent_into_action(intent:str, game:Grid, player:Grid.Player):
    system = f'You are {player.name}. You are playing an escape room game. You must only act on the data presented to you. \
        The board is made up of tiles, each of which has a colour and may contain an object (door or player). \
        You must suggest the move that will most accurately reflect your intent.'
    prompt = [
        {"role": "system", "content": system }, 
        {"role": "user", "content": f'Your intent: {intent}' },
        {"role": "user", "content": f'The current state of the board is below.' },
        {"role": "user", "content": game.to_json() }
        ]
    completion = openai.ChatCompletion.create(
            model='gpt-3.5-turbo', 
            messages=prompt,
            functions=gpt_function_interfaces,
            function_call={"name": "move_player"},
            max_tokens=30)
    response_message = completion["choices"][0]["message"]
    assert response_message.get("function_call")
    return response_message


game_success = game_failure = False
chatroom = ChatRoom()
game = init_game()
views:List[AnyStr] = []
players=[game.Player(name='Lee')]
game.add_object((1, 2), players[0])


rules = 'Your team must open all closed doors. \
        Rules: \
        A door cannot be interacted with directly. \
        The only activity a player can take is to move to a tile that does not have an object (door or player) on it.'

#TODO error handling
while not(game_success or game_failure) : # run until at least one of the final states
    for player in players:
        views.append(get_view_for_player(game, player)) # player based views not yet implemented, perfect vision.
        logging.debug(f'view is {views[-1]}')
        intent = propose_action_for_player(views[-1], player)
        logging.debug(f'Proposed action: {intent}')
        send_message_to_chatroom(intent, chatroom, username=player.name)
        accepted_move = False
        max_tries = 2
        current_try = 0
        while not(accepted_move) and (current_try < max_tries):
            coach_response = critique_action(views[-1], player, intent)
            logging.debug(f'Coach feedback is {coach_response}')
            function_name = coach_response.function_call.name
            function_arguments = json.loads(coach_response.function_call.arguments)
            send_message_to_chatroom(function_arguments['critique'], chatroom, username='coach')
            if function_arguments['approved']:
                accepted_move = True
                # player tries to turn statement into a function call
                action = translate_intent_into_action(intent, game, player)
                logging.debug(f'Player action is {action}')
                function_name = action.function_call.name
                function_arguments = json.loads(action.function_call.arguments)
                move_player(function_arguments['direction'], game, player)
            else:
                logging.debug(f"Coach did not approve intent: {intent} Coach critique: {function_arguments['critique']}")
        if not(accepted_move):
            logging.info('Could not find a move acceptable to the coach.')
            game_failure = True
        if game.where_is(player)[0] == (0,2):
            # that's the blue tile, which should open the door
            game_success = True
if game_success:
    print("WINNER WINNER CHICKEN DINNER!!!!")
else:
    print("Better luck next time.")

if game_failure:
    print("I've fallen and I can't get up.")
else:
    print("All systems nominal.")

# cast: 1 player, 1 coach
# loop  until success() or fail()
    # get_view_for_player(Player)
    # player proposes an action
    # coach critiques action
        # player may retort to continue discussion
    # player move_player()
