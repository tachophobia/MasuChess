import random

import chess
import chess.engine
import chess.pgn
import re
import pyperclip as pc
import asyncio
import os
import sys
import numpy as np

lc0_path = "/Users/noms0/Documents/lc0/lc0.exe"

lc0 = chess.engine.SimpleEngine.popen_uci(lc0_path)
lc0.configure({'Threads': 100})
time_per_move = 0.5


def get_engine_move(board: chess.Board, time=time_per_move):
    global lc0
    try:
        return lc0.play(board, limit=chess.engine.Limit(time=time)).move
    except asyncio.exceptions.TimeoutError:
        print("Asyncio TimeoutError, restarting program")
        os.execv(sys.executable, ['python'] + sys.argv)
        # sys.exit()


def analyze(board: chess.Board, clocks=None):
    if clocks:
        return lc0.analyse(board, limit=chess.engine.Limit(white_clock=min(60, clocks[1]), black_clock=min(60, clocks[0]),
                                                           white_inc=-2, black_inc=-2))['score']
    return lc0.analyse(board, limit=chess.engine.Limit(depth=5))['score']  # depth 6 ~ 1950 elo engine


def weights(rating: int):
    return f"/Users/noms0/Documents/lc0/maia_weights/maia-{rating}.pb.gz"


def get_human_move(engine, board):
    return engine.play(board, limit=chess.engine.Limit(nodes=1)).move


def get_antihuman_moves(engine, board, w: tuple, n: int, threshold=200, clock=None):

    board = board.copy()
    scores = {}

    if not clock:
        clock = 60

    def flip(score):
        return [score.black().score(mate_score=10000), score.white().score(mate_score=10000)][board.turn]

    analysis = lc0.analyse(board, limit=chess.engine.Limit(time=time_per_move),
                           multipv=500)

    highest_cp = analysis[0]['score']

    if clock <= 30:
        return [analysis[0]['pv'][0]]

    # def get_random_not_mate():
    #     random_move = random.choice(list(board.legal_moves))
    #     board.push(random_move)
    #     if not board.is_game_over():
    #         return random_move
    #     else:
    #         return get_random_not_mate()
    #
    # def get_not_mate(analysis):
    #     if analysis:
    #         if flip(analysis[0]['score']) >= 9999:
    #             analysis.pop(0)
    #         else:
    #
    #             return analysis[0]['pv'][0]
    #         return get_not_mate(analysis)
    #     else:
    #         return get_random_not_mate()
    #
    # return [get_not_mate(analysis)]

    for continuation in analysis:
        if np.abs(flip(highest_cp) - flip(continuation['score'])) > threshold:
            break
        else:
            state = board.copy()
            move = continuation['pv'][0]
            state.push(move)
            if not state.is_game_over():
                scores[move] = flip(engine.analyse(state, limit=chess.engine.Limit(nodes=1))['score']), \
                    flip(continuation['score'])
            else:
                return [move]

    sorted_scores = sorted(scores.items(), key=lambda x: w[0] * x[1][0] + w[1] * x[1][1], reverse=True)
    moves, _ = list(zip(*sorted_scores))
    # print(moves, _)
    return list(moves[:min(n, len(list(board.legal_moves)))])


player_elo = 1900  # how to generate best winning chances against this elo
maia = chess.engine.SimpleEngine.popen_uci(lc0_path)
maia.configure({"WeightsFile": weights(player_elo), 'NNCacheSize': 0})

priority_converter = {'being very solid': (0.5, 1), 'being solid': (1, 1), 'being sharp': (1, 0.5),
                      'being very sharp': (1, 0.1)}
priority = priority_converter['being very sharp']

env = chess.Board()

pgn = chess.pgn.Game()
pgn.setup(env)

header_converter = ['You', 'Your opponent']
pgn.headers['White'] = header_converter[not env.turn]
pgn.headers['Black'] = header_converter[env.turn]
pgn.headers['WhiteElo'] = str(player_elo)
pgn.headers['BlackElo'] = str(player_elo)


def expand_pgn(board, depth, expansion_rate=1, parent_node=pgn):
    if board.is_game_over():
        return
    board = board.copy()
    if depth < 1:
        nodes = [parent_node]
        for continuation in range(10):
            if continuation % 2 == 0:
                move = get_engine_move(board)
            else:
                move = get_human_move(maia, board)
            board.push(move)
            nodes.append(nodes[-1].add_variation(move))
            if board.is_game_over():
                del nodes
                return
        del nodes
        return
    for i in get_antihuman_moves(maia, board, priority, expansion_rate):
        board.push(i)
        child_node = parent_node.add_variation(i)
        if not board.is_game_over():
            board = board.copy()
            for j in list({get_antihuman_moves(maia, board, priority_converter['being solid'], n=1)[0],
                           get_human_move(maia, board), get_engine_move(board)}):
                board.push(j)
                second_cousin_node = child_node.add_variation(j)
                expand_pgn(board, depth - 1, max(1, expansion_rate - 1), parent_node=second_cousin_node)
                board.pop()
        board.pop()


if __name__ == "__main__":
    expand_pgn(env, 5)

    # with open("output.pgn", "w") as f:
    #     exporter = chess.pgn.FileExporter(f)
    #     pgn.accept(exporter)

    string_exporter = chess.pgn.StringExporter()
    pgn_string = pgn.accept(string_exporter)
    pgn_string = re.sub(r'\((\s+)?', '(', pgn_string)
    pgn_string = re.sub(r'(\s+)?\)', ')', pgn_string)

    with open("output.pgn", "w") as f:
        f.write(pgn_string)

    pc.copy(pgn_string)
    print(pgn_string)
