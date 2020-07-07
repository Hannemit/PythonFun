import random
import curses
import time
import numpy as np
import tty
import sys
import termios

# TODO: also have a Food class which is basically just a coordinates and a type (less than, greater than)
#  We can then have a Screen class which has Food (composition), it has statements and it has a Zoo.




def UpdateSpeed(nFoodsEaten, factor, init_speed):
    '''
    Function to update the speed of the snake
    Parameters;
        nFoodsEaten: integer, the number of foods eaten up until now
        factor: float, indicates how quickly we increase the speed
        init_speed: float, initial speed of snake

    returns:
        int, new speed of snake
    '''
    nUpdates = nFoodsEaten / 2  # update speed after every 2 foods eaten
    new_speed = int(init_speed * factor ** nUpdates)
    if new_speed < 15:  # maximum speed of 15
        new_speed = 15
    return new_speed


class Snake:

    def __init__(self, up=curses.KEY_UP, down=curses.KEY_DOWN, left=curses.KEY_LEFT, right=curses.KEY_RIGHT):
        # TODO: let snake_type also be part of snake (its shape). Also the snake has a set of colours and it can
        #   change colour or not
        self.snake = []
        self.up = up
        self.down = down
        self.left = left
        self.right = right

    def initialize_snake(self, head_x, head_y):
        # initial snake coordinates
        #snk_x = sw / 4  # x coordinate of snake
        #snk_y = sh / 2  # y coordinate of snake
        self.snake = [
            [head_y, head_x],  # head of snake
            [head_y, head_x - 1],
            [head_y, head_x - 2],
        ]

    def update(self, new_head):
        self.snake.insert(0, new_head)  # insert new head in snake

    def get_new_head(self, key) -> list:
        """
        Function to calculate the new position of the head of the snake
        Parameters;
            key: key that is pressed by user

        return: new coordinates of the head of the snake. Return empty list if no valid key has been pressed
        """
        new_head = [self.snake[0][0], self.snake[0][1]]  # position the new head at the current head

        # update new head
        if key == self.down:
            new_head[0] += 1
        elif key == self.up:
            new_head[0] -= 1
        elif key == self.left:
            new_head[1] -= 1
        elif key == self.right:
            new_head[1] += 1
        else:
            return []  # key other than up, down, left, right is pressed

        return new_head


class Zoo:

    def __init__(self):
        self.snake_list = []
        self.num_snakes = 0

    def add_snake(self, up, down, left, right):
        self.snake_list.append(Snake(up, down, left, right))
        self.num_snakes += 1

    def get_all_coordinates(self):
        if not self.snake_list:
            raise RuntimeError("No snakes present!")

        coordinates = []
        for ii in range(self.num_snakes):
            coordinates.extend(self.snake_list[ii].snake)
        return coordinates


############ ASK USER FOR DIFFICULTY
###################################################################
###################################################################
###################################################################

print('Welcome to Hanne Snake.\nGOAL: eat 40 foods!\n')
print('Food is represented by greater-than-or-equal signs. AVOID the less-than-or-equal signs!!')
print('You are allowed to hit yourself, but not the walls')
print('The number of eaten foods is shown in the top left corner.')
print('What difficulty do you want to play??\nvery hard (v)\nhard (h)\nmedium (m)\n')
print('Give your input (v, h or m): ')

orig_settings = termios.tcgetattr(sys.stdin)
tty.setraw(sys.stdin)
x = 0
while x not in [chr(118), chr(104), chr(109)]:
    x = sys.stdin.read(1)[0]
    print('You pressed %s' % x)
termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig_settings)

if x == 'h':
    factorSpeed = 1.0
    limit_lessthan = 1
    init_speed = 20
elif x == 'v':
    factorSpeed = 0.85
    limit_lessthan = 5
    init_speed = 110
else:
    factorSpeed = 0.9
    limit_lessthan = 3
    init_speed = 180

###################################################################
###################################################################
###################################################################

# INITIALIZE
s = curses.initscr()  # initialise screen. This sets up a bunch of things, always necessary.
curses.curs_set(False)  # set curser to 0 so that it doesn't show up in screen
lessThanCoord = []  # store coordinates of less than or equal signs
nb = 0
# curses.noecho() #don't show in terminal when something is typed

###############
food_type = curses.ACS_GEQUAL
snake_type = curses.ACS_LANTERN
#################

# set up colors
curses.start_color()
curses.init_pair(1, curses.COLOR_RED,
                 curses.COLOR_WHITE)  # define colourpair(1) to be (foreground colour, background colour)
curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
curses.init_pair(6, curses.COLOR_GREEN, curses.COLOR_BLACK)
curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_GREEN)
curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_YELLOW)
curses.init_pair(5, curses.COLOR_RED, curses.COLOR_RED)

# setup window
sh, sw = s.getmaxyx()  # get width and hight
w = curses.newwin(sh, sw, 0, 0)  # new window
w.keypad(1)
w.timeout(init_speed)  # update time


def generate_food(width, height, excluded):
    # TODO: think about this. excluded is initially just the snake, but can later be multiple snakes. It's all the
    #  coordinates that are filled. We need to have a Zoo class which contains snakes, can specify the number of snakes
    #  it creates the snakes and keeps track of the coordinates that are occupied by snakes.
    food = None
    while food is None:  # try to generate new food, if None then try again, etc...
        new_food = [
            random.randint(5, sh - 5),
            random.randint(5, sw - 5)
        ]
        food = new_food if new_food not in snake else None

# add food
food = [sh / 2, sw / 2]  # initialise food position in middle of screen ([y, x]) coordinates
w.addch(food[0], food[1], food_type)  # add food to window

key = curses.KEY_RIGHT
nIter = 0
nFoodsEaten = 0
snake = Snake()
while True:
    # GET KEY
    next_key = w.getch()  # get character that is pressed
    old_key = key
    key = key if next_key == -1 else next_key  # get either nothing or next key. -1 is returned if no input (and then the key remains the same)

    # Move head of snake
    new_head = snake.get_new_head(key)
    if not new_head:
        new_head = snake.get_new_head(old_key)
        key = old_key

    # update snake
    snake.update(new_head)

    if snake.snake[0] == food:
        nFoodsEaten += 1;
        nb = 0
        # TODO: class for printing stuff to screen. Screen.printfood(x) does the num_food_eaten printing
        w.addstr(0, 0, str('%d' % nFoodsEaten))
        w.refresh

        food = None
        while food is None:  # try to generate new food, if None then try again, etc...
            new_food = [
                random.randint(5, sh - 5),
                random.randint(5, sw - 5)
            ]
            food = new_food if new_food not in snake else None

        w.addch(food[0], food[1], food_type)  # add the food to the screen
    else:  # only remove tail if we did not hit some food (we want snake to become longer if we did hit food)
        tail = snake.pop()  # grab tail coordinates (last item in snake) and remove it from snake
        w.addch(tail[0], tail[1], ' ')  # make current tail disappear (as we just moved away)

    # update the snake speed.
    new_speed = UpdateSpeed(nFoodsEaten, factorSpeed, init_speed)
    w.timeout(new_speed)

    # motivational statements
    if nFoodsEaten == 2:
        # w.addstr(0,sw/2-5, 'Keep going!', curses.color_pair(1), curses.A_STANDOUT)
        w.addstr(0, sw / 2 - 5, 'Keep going!', curses.A_STANDOUT)
    elif nFoodsEaten == 20:
        w.addstr(0, sw / 2 - 5, 'Halfway there!', curses.A_STANDOUT)
    elif nFoodsEaten == 30:
        w.addstr(0, sw / 2 - 5, 'You are doing well!!', curses.A_STANDOUT)
    elif nFoodsEaten == 35:
        w.addstr(0, sw / 2 - 5, 'Just a few more!', curses.A_STANDOUT)

    # game is won
    ##############################################################

    if nFoodsEaten == 40:
        w.addstr(sh / 2, sw / 2 - 9, 'CONGRATS! YOU WIN!', curses.color_pair(1))
        w.refresh();
        time.sleep(1)
        for i in range(sw / 8):
            x = i * 8
            for j in range(22):
                w.addstr(j, x, '=^..^=', curses.color_pair(2))
                w.addstr(sh - 1 - j, x, '=^..^=', curses.color_pair(6))
        for i in range(120):
            y = random.randint(1, sh - 1);
            x = random.randint(1, sw - 7)
            w.addstr(y, x, '=^..^=', curses.color_pair(1))
            w.refresh()
            time.sleep(0.1)
        time.sleep(5)
        curses.endwin()
        break

    # game is lost
    ##############################################################
    if snake[0][0] in [0, sh] or snake[0][1] in [0, sw] or tuple(
            snake[0]) in lessThanCoord:  # or snake[0] in snake[1:]:
        for i in range(5):
            w.addstr(sh / 2 + i, sw / 2 - 5, 'YOU LOSE', curses.color_pair(1))
            w.refresh()
            time.sleep(0.2)
        time.sleep(1)

        # print cats
        for i in range(50):
            y = random.randint(1, sh - 1)
            x = random.randint(1, sw - 7)
            w.addstr(y, x, '=^..^=', curses.color_pair(2))
            w.refresh()
        time.sleep(5)
        curses.endwin()
        break

    ##############################################################
    # add new head of snake, change colours
    color = int(np.floor(nIter / 10.0)) % 3 + 3  # every 10 iterations, change colour of snake
    w.addch(snake[0][0], snake[0][1], snake_type, curses.color_pair(color))  # add new head to snake

    # add less than or equal signs after every 5 foods eaten
    if nFoodsEaten % 5 == 0 and nb < limit_lessthan:
        lessthan = None
        while lessthan is None:
            new_lessthan = (
                random.randint(1, sh - 5),
                random.randint(1, sw - 5)
            )

            if new_lessthan not in snake \
                    and new_lessthan[0] not in range(snake[0][0] - 5, snake[0][0] + 5) \
                    and new_lessthan[1] not in range(snake[0][1] - 5, snake[0][1] + 5):
                lessthan = new_lessthan
            else:
                lessthan = None
        w.addch(lessthan[0], lessthan[1], curses.ACS_LEQUAL)
        lessThanCoord.append(lessthan)
        nb += 1

    nIter += 1