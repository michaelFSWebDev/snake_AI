from turtle import done
import torch
import random
import numpy as np
from collections import deque
from game import SnakeGameAi, Direction, Point


MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001

class Agent:

    def __init__(self):
        self.n_games = 0
        self.epsilon = 0 # randomness
        self.gamma = 0 # discount rate
        self.memory = deque(maxlen=MAX_MEMORY) 
        self.model = None # TODO:
        self.trainer = None # TODO: trainer

    def get_state(self, game):
        head = game.snake[0]
        point_l = Point(head.x -20, head.y)
        point_r = Point(head.x +20, head.y)
        point_u = Point(head.x, head.y -20)
        point_d = Point(head.x, head.y + 20)

        dir_l = game.direction == Direction.LEFT
        dir_r = game.direction == Direction.RIGHT
        dir_u = game.direction == Direction.UP
        dir_d = game.direction == Direction.DOWN

        state = [
            # Danger straight
            (dir_r and game.is_collosion(point_r)) or
            (dir_l and game.is_collosion(point_l)) or
            (dir_u and game.is_collosion(point_u)) or
            (dir_d and game.is_collosion(point_d)),
            
            # Danger right
            (dir_u and game.is_collosion(point_r)) or
            (dir_d and game.is_collosion(point_l)) or
            (dir_l and game.is_collosion(point_u)) or
            (dir_r and game.is_collosion(point_d)),
            
            # Danger right
            (dir_d and game.is_collosion(point_r)) or
            (dir_u and game.is_collosion(point_l)) or
            (dir_r and game.is_collosion(point_u)) or
            (dir_l and game.is_collosion(point_d)),

            # move direction
            dir_l,
            dir_r,
            dir_u,
            dir_d,

            # Food location

            game.food.x < game.head.x,
            game.food.x > game.head.x,
            game.food.y < game.head.y,
            game.food.y > game.head.y,
        ]
        return np.array(state, dtype=int)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done)) # popleft if MAX_MEMORY is reached


    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE) # list of tuples
        else:
            mini_sample = self.memory
        
        states, actions, rewards, next_states, dones = zip(*mini_sample) # zip extracts the actions etc and puts it in our new statements from the mini_sample
        self.trainer.train_step(states, actions, rewards, next_states, dones)

        # Can be done in a for loop as well
        # for state, action, reward, next_state, done in mini_sample:
            # self.trainer.train_step(state, action, reward, next_state, done)
    
    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        # random move : Trade off exploration / exploitation
        self.epsilon = 80 - self.n_games
        final_move = [0,0,0]
        if random.randint(0, 200) < self.epsilon:
            move = random.randint(0,2)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model.predict(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1
        return final_move
        

def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game = SnakeGameAi()
    while True:
        # get old state
        state_old = agent.get_state(game)

        # get the move
        final_move = agent.get_action(state_old)

        # preform move
        reward, done, score = game.play_step(final_move)
        state_new = agent.get_state(game)

        # train short mem
        agent.train_short_memory(state_old, final_move, reward, state_new, done)

        # remember
        agent.remember(state_old, final_move, reward, state_new, done)

        if done:
            # train the long memeory, plot results
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            if score > record:
                record = score
                # agent.model.save()

            print('Game: ', agent.n_games, 'Score: ', score, 'Record: ', record)

            # TODO: plot



if __name__ == '__main__':
    train()