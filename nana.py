import numpy as np
from itertools import combinations, groupby

# Defining constants
IS_PAINT = 1
IS_BLANK = 0
IS_CROSS = -1

DEBUG = False

# Defining helper classes
class PuzzleException(Exception):
    pass
    
class ColisionError(PuzzleException):
    pass
    
class NoOptionsError(PuzzleException):
    def __init__(self, row_or_column, number):
        super().__init__("{} {} has no fitting combinations left!".format(row_or_column, number))
        
    
clues_horz = []
clues_vert = []

# Read puzzle from file
puzzle_file = "puzzles\pokemon_x.non"
with open(puzzle_file, "r") as f:
    reading = 0
    #buff = 0
    for line in f:
        line_tokens = line.split(' ')
        if (len(line_tokens) == 0) or (line_tokens[0] == '\n'): #buff == 0 and 
            reading = 0
        else:    
            if reading == 0:
                if line_tokens[0] == 'width':
                    w = int(line_tokens[1])
                elif line_tokens[0] == 'height':
                    h = int(line_tokens[1])
                elif line_tokens[0] == 'rows' or line_tokens[0] == 'rows\n':
                    reading = 1
                elif line_tokens[0] == 'columns' or line_tokens[0] == 'columns\n':
                    reading = 2
                else:
                    pass
            elif reading == 1: # rows
                #print("Reading rows from " + line)
                if line[-1] == '\n':
                    clues_horz.append([int(v) for v in line[:-1].split(',')])
                else:
                    clues_horz.append([int(v) for v in line.split(',')])
            elif reading == 2: # columns
                if line[-1] == '\n':
                    clues_vert.append([int(v) for v in line[:-1].split(',')])
                else:
                    clues_vert.append([int(v) for v in line.split(',')])

if DEBUG:                    
    print(clues_horz)
    print(clues_vert)

# Defining function to print board
def present_board(board):
    symbols = {IS_PAINT: '#', IS_BLANK: '?', IS_CROSS: ' '}
    for line in board.tolist():
        line_trans = []
        for element in line:
            line_trans.append(symbols[element])
        print('\t' + '|'.join(line_trans))

# Define the board size
board_size = (h,w)

# Sets of clues (will be read from file?) 
#clues_horz = [[3],[2,1],[3,2],[2,2],[6],[1,5],[6],[1],[2]]
#clues_vert = [[1,2],[3,1],[1,5],[7,1],[5],[3],[4],[3]]

# Format reading = http://scc-forge.lancaster.ac.uk/open/nonogram/fmt2 ; https://github.com/mikix/nonogram-db/blob/master/FORMAT.md

# Make sure we have clues for all lines and columns
assert len(clues_horz) == board_size[0], "Expected {} horizontal clues, got {}".format(board_size[0], len(clues_horz))
assert len(clues_vert) == board_size[1], "Expected {} vertical clues, got {}".format(board_size[1], len(clues_vert))

# Create the board, init with blanks
board = np.zeros(board_size, dtype=int)
board += IS_BLANK

# Create all possible lines and columns given the clues and the board size
def partitions(n, t):
    assert(0 <= n <= t)
    def intervals(c):
        last = 0
        for i in c:
            yield i - last
            last = i
        yield t - last
    for c in combinations(range(1, t), n - 1):
        yield list(tuple(intervals(c)))
        
def create_list(width, clues):
    for space_sequence in partitions(len(clues) + 1, 2 + width - sum(clues)):
        #res = []
        res = [IS_CROSS] * (space_sequence[0] - 1) # Needs to remove 1 from each end*
        res += [IS_PAINT] * clues[0]
        for i in range(len(space_sequence) - 2):
            res += [IS_CROSS] * space_sequence[i + 1] # Create alternating segments of paint and cross
            res += [IS_PAINT] * clues[i + 1]
        res += [IS_CROSS] * (space_sequence[-1] - 1) # *Here too
        yield res

# Creating lines
def create_all_1d(width, all_clues):
    for clue in all_clues:
        k = list(create_list(width, clue))
        k.sort()
        yield list(k for k,_ in groupby(k))
        
track_horz = list(create_all_1d(board_size[1], clues_horz))
track_vert = list(create_all_1d(board_size[0], clues_vert))

if DEBUG:
    print(track_horz)
    print(track_vert)

def check_colision(current_state, match):
    assert len(current_state) == len(match)
    for i in range(len(current_state)):
        if current_state[i] != IS_BLANK and match[i] != IS_BLANK and current_state[i] != match[i]:
            raise ColisionError

stalemate = False
victory = False
while (not stalemate) and (not victory):
    try:
        _last_board_state = np.copy(board)
        # For each column, check if fits given current board state
        for column_match_i in range(len(track_vert)):
            _pop_list = []
            for indiv_match_i in range(len(track_vert[column_match_i])):
                try:
                    check_colision(board[:,column_match_i], track_vert[column_match_i][indiv_match_i])
                except ColisionError:
                    _pop_list = [indiv_match_i] + _pop_list
            # Remove all that dont fit current board state
            for _pop_id in _pop_list:
                track_vert[column_match_i].pop(_pop_id)

            if len(track_vert[column_match_i]) == 0: # Error
                raise NoOptionsError("Column", column_match_i + 1)
                
            # Given the surviving options, find intersections between them
            _new_option = track_vert[column_match_i][0]
            if len(track_vert[column_match_i]) > 0:
                for surviving_match in track_vert[column_match_i][1:]:
                    _new_option = np.where(_new_option == np.array(surviving_match), surviving_match, IS_BLANK)
                
            board[:,column_match_i] = _new_option
        print("Board after column analysis:")
        present_board(board) 
        print("----------------------------")
        
        # For each row, check if fits given current board state
        for row_match_i in range(len(track_horz)):
            _pop_list = []
            for indiv_match_i in range(len(track_horz[row_match_i])):
                try:
                    check_colision(board[row_match_i,:], track_horz[row_match_i][indiv_match_i])
                except ColisionError:
                    _pop_list = [indiv_match_i] + _pop_list
            # Remove all that dont fit current board state
            for _pop_id in _pop_list:
                track_horz[row_match_i].pop(_pop_id)

            if len(track_horz[row_match_i]) == 0: # Error
                raise NoOptionsError("Row", row_match_i + 1)
                
            # Given the surviving options, find intersections between them
            _new_option = track_horz[row_match_i][0]
            if len(track_horz[row_match_i]) > 0:
                for surviving_match in track_horz[row_match_i][1:]:
                    _new_option = np.where(_new_option == np.array(surviving_match), surviving_match, IS_BLANK)
            
            board[row_match_i,:] = _new_option
        print("Board after row analysis:")
        present_board(board) 
        print("----------------------------")
        if not np.any(board != _last_board_state):
            stalemate = True
        if not np.any(board == IS_BLANK):
            victory = True
    except NoOptionsError as e:
        print(e)
        print("Check if the clues are correct then try again.")
        break
    except Exception:
        print("Unknown error. Maybe puzzle is not solvable? Check if the clues are correct then try again.")
        break
if stalemate:
    print("Error: Board state did not change!")