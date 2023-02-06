import time

import chess.engine
import numpy as np

from developer import *
import requests
import json


def get_bot_move(position, clock_left):
    return get_antihuman_moves(lc0, position, w=priority, n=1, clock=clock_left)[0]


LICHESS_HOST = "https://lichess.org"

api_key = "lip_VgQ9K2dxloiReTRhY1Qb"

headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/x-www-form-urlencoded'}
response = requests.get(f"{LICHESS_HOST}/api/stream/event", headers=headers, stream=True)
print(response)


def make_move(game_id, uci):
    return requests.post(f"{LICHESS_HOST}/api/bot/game/{game_id}/move/{uci}",
                         headers=headers)


def write_in_chat(game_id, message):
    chat = requests.post(f"{LICHESS_HOST}/api/board/game/{game_id}/chat", headers=headers, data={'text': message,
                                                                                                 'room': 'player'})
    if chat.status_code == 200:
        return chat.json()
    else:
        print("Request failed with status code", chat)
        return None


def stream_incoming_events():
    global response, headers
    event = b""

    for line in response.iter_content():
        if line:
            if type(event) == bytes:
                event = event + line
            else:
                event = line
            try:
                event = json.loads(event.decode("utf-8"))
            except (json.decoder.JSONDecodeError, UnicodeDecodeError):
                continue

            if event['type'] == 'challenge':
                challenge = event['challenge']
                if challenge['speed'] != 'correspondence' and challenge['variant']['key'] == 'standard' and challenge[
                    'speed'] != 'rapid':
                    response = requests.post(f"{LICHESS_HOST}/api/challenge/{challenge['id']}/accept", headers=headers)
                    print(f"Accepted challenge from {challenge['challenger']['id']}")
                elif challenge['variant']['key'] != 'standard':
                    response = requests.post(f"{LICHESS_HOST}/api/challenge/{challenge['id']}/decline",
                                             headers=headers, data={'reason': "variant"})
                else:
                    response = requests.post(f"{LICHESS_HOST}/api/challenge/{challenge['id']}/decline",
                                             headers=headers, data={'reason': "timeControl"})

            elif event["type"] == 'gameStart':

                game_id = event['game']['gameId']
                color = event['game']['color']

                # write_in_chat(game_id, f"Hello {event['game']['opponent']['username']}. I am programmed to "
                #                        f"exploit the weaknesses of players your level, "
                #                        f"even if it means not always playing the best move.")

                # write_in_chat(game_id, "If you would prefer to practice against a certain elo, type that elo ("
                #                        "1100-1900) in chat.")

                game = requests.get(f"{LICHESS_HOST}/api/bot/game/stream/{event['game']['gameId']}", headers=headers,
                                    stream=True)

                for move in game.iter_lines():
                    if move:
                        move = move.decode('utf-8')
                        game_state = json.loads(move)
                        try:
                            moves_made = game_state['moves']
                            move_time = game_state[['btime', 'wtime'][color == 'white']] / 1000
                        except KeyError:
                            try:
                                moves_made = game_state['state']['moves']
                                move_time = game_state['state'][['btime', 'wtime'][color == 'white']] / 1000
                            except KeyError:
                                continue

                        board = chess.Board()
                        for m in moves_made.split():
                            board.push_uci(m)
                        if not board.is_game_over() and board.turn == [0, 1][color == 'white']:
                            # start = time.time()
                            make_move(game_id, get_bot_move(board, move_time).uci())
                            # print(time.time() - start)

                game.close()


stream_incoming_events()

