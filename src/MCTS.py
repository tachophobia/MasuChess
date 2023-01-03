import datetime
import numpy as np
import collections
import pickle
from preprocessing import *


class Node:
    def __init__(self, state, action, parent=None):
        self.state = state
        if self.state.turn == chess.BLACK:
            self.state.apply_mirror()
        self.prior_action = action
        self.parent = parent

        self.leaf = True
        self.children = {}

        self.child_total_values = np.zeros([1880], dtype=np.float32)
        self.child_n_visits = np.zeros([1880], dtype=np.float32)
        self.child_priors = np.zeros([1880], dtype=np.float32)

        self.possible_actions = []

    @property
    def n_visits(self):
        return self.parent.child_n_visits[self.prior_action]

    @n_visits.setter
    def n_visits(self, value):
        self.parent.child_n_visits[self.prior_action] = value

    @property
    def total_value(self):
        return self.parent.child_total_values[self.prior_action]

    @total_value.setter
    def total_value(self, value):
        self.parent.child_total_values[self.prior_action] = value

    def child_Q(self):
        return self.child_total_values / (1 + self.child_n_visits)

    def child_U(self):
        return np.sqrt(self.n_visits) * (abs(self.child_priors) / (1 + self.child_n_visits))

    def best_child(self):
        if self.possible_actions:
            best_move = self.child_Q() + self.child_U()
            best_move = self.possible_actions[np.argmax(best_move[self.possible_actions])]
        else:
            best_move = np.argmax(self.child_Q() + self.child_U())
        return best_move

    def select_leaf(self):
        current = self
        while not current.leaf:
            best_move = current.best_child()
            current = current.add_child(best_move)
        return current

    @staticmethod
    def add_dirichlet_noise(actions, child_priors, x=0.75, c=0.3):
        valid_child_priors = child_priors[actions]
        valid_child_priors = x * valid_child_priors + (1 - x) * np.random.dirichlet(np.zeros([len(valid_child_priors)],
                                                                                             dtype=np.float32) + c)
        child_priors[actions] = valid_child_priors
        return child_priors

    def expand(self, child_priors):
        self.leaf = False
        # create list of possible actions (their indexes)
        legal_actions = []
        c_p = child_priors
        # check for terminal state: if true, leaf = True
        if not self.state.is_game_over():
            for action in list(self.state.legal_moves):
                legal_actions.append(to_index(action.uci()))
        else:
            self.leaf = True
        # update possible actions
        self.possible_actions = legal_actions
        # mask illegal actions
        for action_index in range(len(child_priors)):
            if action_index not in legal_actions:
                c_p[action_index] = 0.
        # add dirichlet noise to root node's child priors
        if self.parent.parent is None:
            c_p = self.add_dirichlet_noise(legal_actions, c_p)
        # update child priors
        self.child_priors = c_p

    def add_child(self, move):
        if move not in self.children:
            state_copy = self.state.copy()
            state_copy.push_uci(to_uci(move))
            self.children[move] = Node(state_copy, move, parent=self)
        return self.children[move]

    def backpropagate(self, value_estimate: float):
        current = self
        while current.parent is not None:
            current.n_visits += 1
            turn = current.state.turn
            if turn == 1:
                current.total_value += (1 * value_estimate)
            else:
                current.total_value += (-1 * value_estimate)
            current = current.parent


class EmptyNode(object):
    def __init__(self):
        self.parent = None
        self.child_total_values = collections.defaultdict(float)
        self.child_n_visits = collections.defaultdict(float)


def tree_search(state, model, iterations):
    root = Node(state, action=None, parent=EmptyNode())

    for _ in range(iterations):
        leaf = root.select_leaf()
        child_priors, value_estimate \
            = model(preprocess(state))
        if leaf.state.is_game_over():
            leaf.backpropagate(value_estimate)
        leaf.expand(child_priors)
        leaf.backpropagate(value_estimate)
    return np.argmax(root.child_n_visits), root


def get_policy(root):
    policy = np.zeros([1880], dtype=np.float32)
    for index in np.where(root.child_n_visits != 0)[0]:
        policy[index] = root.child_n_visits[index] / root.child_n_visits.sum()
    return policy


def save(data, directory):
    with open(directory, 'wb') as f:
        pickle.dump(data, f)


def load(directory):
    with open(directory, 'rb') as f:
        return pickle.load(f)


move_vector = load('data/permutations.dat')


def to_index(move):
    return move_vector.index(move)


def to_uci(index):
    return move_vector[index]


def self_play(model, n_games: int):
    env = chess.Board()
    for game in range(0, n_games):
        env.reset()
        dataset = []
        value = 0
        turn = -1
        while not env.is_game_over():
            turn += 1
            best_move, root = tree_search(env.copy(), model, 800)
            env.push_uci(to_uci(best_move))
            policy = get_policy(root)
            dataset.append([env.copy(), policy])
            env.apply_mirror()
        if turn % 2 == 0:
            value = 1
        elif turn % 2 == 1:
            value = -1

        df = []
        for i, data in enumerate(dataset):
            s, p = data
            if i == 0:
                df.append([s, p, 0])
            else:
                df.append([s, p, value])
        del dataset
        save('dframe_%s' % (datetime.datetime.today().strftime('%Y_%m_%d')), df)


def dummy_model(_):
    return np.random.random_sample(1880), np.random.uniform(-1, 1)


if __name__ == "__main__":
    self_play(dummy_model, 1)
