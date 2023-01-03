import torch
import chess


def preprocess(board, N=8):
    player_planes = []
    player_color_planes = torch.zeros((N, N))
    action_space_planes = []  # Define new list to hold action space matrices
    # Assign values to each piece type
    values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 100}
    for piece_type in chess.PIECE_TYPES:
        player_plane = torch.zeros((N, N))
        action_space_plane = torch.zeros((N, N))  # Initialize action space matrix for current piece type
        for square in board.pieces(piece_type, chess.WHITE):
            player_plane[square // N, square % N] = values[piece_type]
            action_space = list(board.attacks(square))
            for action_square in action_space:
                action_space_plane[action_square // N, action_square % N] = 1
        player_planes.append(player_plane)
        action_space_planes.append(action_space_plane)

        player_color_planes += player_plane
    player_planes.append(player_color_planes)

    opponent_planes = []
    opponent_color_planes = torch.zeros((N, N))
    for piece_type in chess.PIECE_TYPES:
        opponent_plane = torch.zeros((N, N))
        action_space_plane = torch.zeros((N, N))
        for square in board.pieces(piece_type, chess.BLACK):
            opponent_plane[square // N, square % N] = values[piece_type]
            action_space = list(board.attacks(square))
            for action_square in action_space:
                action_space_plane[action_square // N, action_square % N] = 1
        opponent_planes.append(opponent_plane)
        action_space_planes.append(action_space_plane)

        opponent_color_planes += opponent_plane
    opponent_planes.append(opponent_color_planes)

    planes = torch.cat([torch.stack(planes) for planes in [player_planes, opponent_planes, action_space_planes]],
                       dim=0)
    return planes