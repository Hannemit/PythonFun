import random
import curses
import time
import numpy as np
import tty
import sys
import termios

# TODO: also have a Food class which is basically just a coordinates and a type (less than, greater than)
#  We can then have a Screen class which has Food (composition), it has statements and it has a Zoo.


FOOD_TYPE = curses.ACS_GEQUAL
snake_type = curses.ACS_LANTERN
MAX_SPEED = 15

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
    nUpdates = nFoodsEaten // 2  # update speed after every 2 foods eaten
    new_speed = int(init_speed * factor ** nUpdates)
    if new_speed < 15:  # maximum speed of 15
        new_speed = 15
    return new_speed


def get_user_difficulty_input() -> str:
    user_input = 0
    while user_input not in [chr(118), chr(104), chr(109)]:
        user_input = sys.stdin.read(1)[0]
        print(f"You pressed {user_input}")
    return user_input


class Snake:

    def __init__(self, up, down, left, right, init_speed, factor_speed_increase, ):
        # TODO: let snake_type also be part of snake (its shape). Also the snake has a set of colours and it can
        #   change colour or not
        self.snake_body = []
        self.up = up
        self.down = down
        self.left = left
        self.right = right
        self.speed = init_speed
        self.factor_speed_increase = factor_speed_increase
        self.last_key_pressed = self.left
        self.num_food_eaten = 0
        # TODO: each snake starts with an initial direction, and has a self.last_key, the last key that was pressed
        #   then when a new key gets pressed we just apply that to all snakes, and if there's a snake for which that
        #   key is actually an input then it updates last_key and it moves, otherwise it just keeps moving into lastkey
        #   so there's a move() function on the screen or whatever and it moves all snakes in a loop. I guess the snake
        #   itself should have a move() too and it takes in a new key and checks it against its own internal keys.

    def initialize_snake(self, head_x, head_y):
        # initial snake coordinates
        #snk_x = sw / 4  # x coordinate of snake
        #snk_y = sh / 2  # y coordinate of snake
        self.snake_body = [
            [head_y, head_x],  # head of snake
            [head_y, head_x - 1],
            [head_y, head_x - 2],
        ]

    def increase_speed(self):
        self.speed = max(MAX_SPEED, self.speed * self.factor_speed_increase)

    def add_new_head(self, new_head_):
        self.snake_body.insert(0, new_head_)  # insert new head in snake

    def get_new_head(self, key_pressed) -> list:
        """
        Function to calculate the new position of the head of the snake
        Parameters;
            key_pressed: the key that is pressed by user

        return: new coordinates of the head of the snake. Return empty list if no valid key has been pressed
        """
        new_head = [self.snake_body[0][0], self.snake_body[0][1]]  # position the new head at the current head

        # update new head
        if key_pressed == self.down:
            new_head[0] += 1
        elif key_pressed == self.up:
            new_head[0] -= 1
        elif key_pressed == self.left:
            new_head[1] -= 1
        elif key_pressed == self.right:
            new_head[1] += 1
        else:
            return self.get_new_head(self.last_key_pressed)  # key other than up, down, left, right is pressed

        self.last_key_pressed = key_pressed
        return new_head

    def move(self, new_key):
        new_head_position = self.get_new_head(new_key)
        self.add_new_head(new_head_position)

    def get_tail(self):
        return self.snake_body.pop()


class MediumSnake(Snake):

    def __init__(self, up, down, left, right):
        super().__init__(up, down, left, right, 180, 0.9)


class HardSnake(Snake):

    def __init__(self, up, down, left, right):
        super().__init__(up, down, left, right, 20, 1)


class VeryHardSnake(Snake):

    def __init__(self, up, down, left, right):
        super().__init__(up, down, left, right, 110, 0.85)


class Zoo:

    def __init__(self, width, height):
        self.snake_list = []
        self.num_snakes = 0
        self.width = width
        self.height = height

    def get_snake_init_coords(self):
        if self.num_snakes == 0:
            return self.width // 4, self.height // 2
        elif self.num_snakes == 1:
            return self.width // 2, self.height // 5
        else:
            raise NotImplemented("Do some randomized initial position of more snakes!!")

    def add_snake(self, type_snake, up, down, left, right):
        if type_snake == "h":
            snake = HardSnake(up, down, left, right)
        elif type_snake == "m":
            snake = MediumSnake(up, down, left, right)
        elif type_snake == "v":
            snake = VeryHardSnake(up, down, left, right)
        else:
            raise ValueError(f"unknown type snake {type_snake}")

        self.num_snakes += 1
        snake_start_x, snake_start_y = self.get_snake_init_coords()
        snake.initialize_snake(snake_start_x, snake_start_y)

        self.snake_list.append(snake)

    def get_all_coordinates(self):
        if not self.snake_list:
            raise RuntimeError("No snakes present!")

        coordinates = []
        for ii in range(self.num_snakes):
            coordinates.extend(self.snake_list[ii].snake_body)
        return coordinates


class Screen:
    # TODO: this won't work, I had assumed somewhere that snake is just a 'list of coordinates', but
    #   actually we have x and y coordinates... I guess in theory I could map every (x,y) to a single number
    #   so (0,0) --> 0, (0, 1) --> 1, etc.. etc.. so flatten the screen.. will make things easier maybe?
    #   this is a problem atm for checking whether things are in the snakes, and also in the obstacles and foods and stuff

    def __init__(self):
        self.window = None
        self.zoo = None
        self.food = None

        orig_settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig_settings)

        self.screen = curses.initscr()  # initialise screen.
        self.height, self.width = self.get_screen_dimensions()

        curses.curs_set(False)  # set cursor to 0 so that it doesn't show up in screen
        curses.noecho()  # don't show in terminal when something is typed
        self.set_up_colours()

        self.obstacle_coordinates = []  # store coordinates of the obstacles that kill the snake

        # create initial window with some food in it
        self.init_window()
        self._add_food_to_screen(self.height // 2, self.width // 2)

    def add_zoo(self, zoo):
        self.zoo = zoo

    def init_window(self):
        self.window = curses.newwin(self.height, self.width, 0, 0)
        self.window.keypad(True)
        self.window.timeout(10)  # TODO: what do here? Need difficulty?? Set later?

    def get_new_object_position(self, x_bounds, y_bounds, not_allowed_in):
        proposed_object = not_allowed_in[0]
        while proposed_object in not_allowed_in:
            proposed_object = [
                random.randint(x_bounds[0], x_bounds[1]),
                random.randint(y_bounds[0], y_bounds[1])
            ]

        return proposed_object

    def get_food_position(self):
        snake_coordinates = self.zoo.get_all_coordinates()
        return self.get_new_object_position([5, self.height - 5], [5, self.width - 5], snake_coordinates)

    def _add_object_to_screen(self, object_x, object_y, object_id: str):
        self.window.addch(object_x, object_y, object_id)
        # self.food = [food_x, food_y]

    def add_food(self):
        food = self.get_food_position()
        self._add_object_to_screen(food[0], food[1], FOOD_TYPE)

    def move_snakes(self, new_key):
        # TODO: do we first want to move all snakes, and then check whether food is eaten and
        #   regenerate? Otherwise the new food might be exactly in front of a snake who then
        #   immediately eats it?
        for single_snake in self.zoo.snake_list:
            single_snake.move(new_key)

            if single_snake[0] == self.food:
                # food has been eaten
                self.add_food()  # snake has grown, do not remove tail

                # every 5 foods, update speed of snake
                single_snake.num_food_eaten += 1
                if single_snake.num_food_eaten % 5 == 0:
                    single_snake.increase_speed()
            else:
                tail = single_snake.get_tail()
                self.remove_pixel(tail)  # snake moves forward, remove tail

    def remove_pixel(self, pixel_coord):
        self.window.addch(pixel_coord[0], pixel_coord[1], ' ')

    def update_window(self):
        pass

    def add_obstacle(self):
        # TODO: also make obstacle appear not directly in front of snake!!
        snake_coordinates = self.zoo.get_all_coordinates()
        obstacle_pos = self.get_new_object_position([1, self.height - 5], [1, self.width - 5], snake_coordinates)
        self._add_object_to_screen(obstacle_pos[0], obstacle_pos[1], curses.ACS_LEQUAL)
        self.obstacle_coordinates.append(obstacle_pos)

    def get_screen_dimensions(self):
        return self.screen.getmaxyx()

    def print_starting_message(self) -> None:
        print('Welcome to Hanne Snake.\nGOAL: eat 40 foods!\n')
        print('Food is represented by greater-than-or-equal signs. AVOID the less-than-or-equal signs!!')
        print('You are allowed to hit yourself, but not the walls')
        print('The number of eaten foods is shown in the top left corner.')
        print('What difficulty do you want to play??\nvery hard (v)\nhard (h)\nmedium (m)\n')
        print('Give your input (v, h or m): ')

    def print_win_message(self) -> None:
        self.window.addch(self.height // 2, self.width // 2 - 9, "CONGRATS! YOU WIN!")
        time.sleep(5)

    def print_lost_message(self):
        self.window.addch(self.height // 2, self.width // 2 - 9, "YOU LOSE")
        time.sleep(5)

    @staticmethod
    def set_up_colours():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED,
                         curses.COLOR_WHITE)  # define colourpair(1) to be (foreground colour, background colour)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_GREEN)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_YELLOW)
        curses.init_pair(5, curses.COLOR_RED, curses.COLOR_RED)

    def game_lost(self):
        # check whether game is lost, i.e. check whether snake in obstacle or wall
        snake_coordinates = self.zoo.get_all_coordinates()

        # check hitting wall TODO: only need to check new heads
        boundaries = [0, self.width, self.height]
        if any(boundary in snake_coordinates for boundary in boundaries):
            return True

        # check obstacles
        if any(obs in snake_coordinates for obs in self.obstacle_coordinates):
            return True

        return False


def play_game():

    # set up screen and zoo
    screen = Screen()
    zoo = Zoo(screen.width, screen.height)

    # print user message, get user input
    screen.print_starting_message()
    difficulty = get_user_difficulty_input()
    # TODO: get number of snakes here too. Start with option of 1 and 2

    # add snakes to zoo
    zoo.add_snake(difficulty, curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT)

    # add zoo to screen
    screen.add_zoo(zoo)

    old_key = curses.KEY_RIGHT
    while True:
        new_key = screen.window.getch()  # get character that is pressed
        new_key = old_key if new_key == -1 else new_key  # get either nothing or next key. -1 is returned if no input (and then the key remains the same)

        # Move head of snake
        screen.move_snakes(new_key)

        # update window refresh rate
        screen.window.timeout()

        # add obstacles
        if screen.zoo.snake_list[0].num_food_eaten % 2 == 0:
            screen.add_food()

        # game won
        if screen.zoo.snake_list[0].num_food_eaten == 20:
            screen.print_win_message()
            curses.endwin()
            break

        # game lost
        if screen.game_lost:
            screen.print_lost_message()
            curses.endwin()
            break



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

key = curses.KEY_RIGHT

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