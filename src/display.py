import random
import tkinter as tk
from time import sleep
import chess


class Display:
    def __init__(self, board, C: int):
        self.window = tk.Tk()
        self.window.title("Chess Board")
        self.C = C
        self.board = board

        self.board_display = tk.Canvas(self.window, width=self.C * 400, height=self.C * 400)
        self.board_display.pack()

        self.plot()

        self.window.after(0, self.window.mainloop)

    def update(self, move):
        self.board.push_uci(move)
        self.plot()

    def reset(self):
        self.board.reset()

    def plot(self):
        self.board_display.delete("all")
        state = self.board.copy()
        state.apply_mirror()
        for i in range(8):
            for j in range(8):
                if (i + j) % 2 == 0:
                    color = "white"
                else:
                    color = "gray"
                self.board_display.create_rectangle(self.C * 50 * j, self.C * 50 * i, self.C * 50 * (j + 1),
                                                    self.C * 50 * (i + 1), fill=color)
        for i in range(8):
            for j in range(8):
                piece = state.piece_at(8 * i + j)
                if piece is not None:
                    if piece.color == chess.WHITE:
                        color = "blue"
                    else:
                        color = "red"
                    self.board_display.create_text(self.C * (25 + 50 * j), self.C * (25 + 50 * i),
                                                   text=piece.unicode_symbol(),
                                                   font=("Arial", 24 * self.C),
                                                   fill=color)
        self.window.update()



