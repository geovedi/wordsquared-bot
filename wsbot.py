#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import re
import json
import sys
import random
import collections
import operator
import struct
import logging
import time
import traceback

# Must be an odd number
ODD_NUMBER = 31

USERNAME = 'username'
PASSWORD = 'password'

# 1: Display standard debugging message
# 2: Display verbose message from 'requests'
# 3: Display verbose debugging message
DEBUG_LEVEL = 1
DEBUG = True
# Timeout for requests()
TIMEOUT = 30


# Utils
formatter = logging.Formatter('%(asctime)-6s: %(name)s - '
                              '%(levelname)s - %(message)s')

consoleLogger = logging.StreamHandler()
consoleLogger.setFormatter(formatter)
logging.getLogger('').addHandler(consoleLogger)

fileLogger = logging.FileHandler(filename='logs/wordsquared.log')
fileLogger.setLevel(logging.INFO)
fileLogger.setFormatter(formatter)
logging.getLogger('').addHandler(fileLogger)

logger = logging.getLogger('wordsquared-bot')
logger.setLevel(logging.INFO)
if DEBUG:
    logger.setLevel(logging.DEBUG)


def check_even(number):
    if number % 2 == 0:
        return True
    else:
        return False


def get_median(numeric_list):
    sorted_list = sorted(numeric_list)
    if not check_even(len(sorted_list)):
        return sorted_list[(len(sorted_list) + 1) / 2 - 1]
    else:
        lower = sorted_list[len(sorted_list) / 2 - 1]
        upper = sorted_list[len(sorted_list) / 2]
        return float((lower + upper)) / 2


# Variables
if DEBUG and DEBUG_LEVEL >= 2:
        REQUESTS_CONFIG = {'verbose': sys.stderr}
else:
        REQUESTS_CONFIG = {}

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3)' \
             ' AppleWebKit/536.6 (KHTML, like Gecko)' \
             ' Chrome/20.0.1096.1 Safari/536.6'

WSQD = 'http://wordsquared.com'

WIDTH = ODD_NUMBER
HEIGHT = ODD_NUMBER
BOARD_SIZE = WIDTH * HEIGHT
MEDIAN_BOARD = get_median(xrange(BOARD_SIZE))
MEDIAN_WIDTH = get_median(xrange(WIDTH))
MEDIAN_HEIGHT = get_median(xrange(HEIGHT))
START = MEDIAN_BOARD
HORIZONTAL = 1
VERTICAL = 2
DIRECTION = {HORIZONTAL: (1, 0), VERTICAL: (0, 1)}
# Compute move based on the opposite direction
# e.g. if the location shift to NW, the move start computed from SE
LOCATION_START = {
    'SE': 0,
    'S':  MEDIAN_WIDTH,
    'SW': WIDTH,
    'E':  1 + (MEDIAN_HEIGHT * HEIGHT),
    'W':  WIDTH + (MEDIAN_HEIGHT * HEIGHT),
    'NE': 1 + (WIDTH * HEIGHT) - WIDTH,
    'N':  (WIDTH * HEIGHT) - MEDIAN_WIDTH,
    'NW': (WIDTH * HEIGHT),
}
RACK_SIZE = 7
BINGO = 0
EMPTY = '.'
WILD = '?'
SKIP = '-'
SENTINEL = '$'
LETTER_MULTIPLIER = [
    1, 1, 2, 1, 1, 1, 2, 1, 2, 1, 1, 1, 2, 1,
    1, 2, 1, 1, 1, 3, 1, 1, 1, 3, 1, 1, 1, 2,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1,
    1, 1, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1,
    1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2,
    1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1,
    1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2,
    1, 1, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1,
    1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 2, 1, 1, 1, 3, 1, 1, 1, 3, 1, 1, 1, 2,
    1, 1, 2, 1, 1, 1, 2, 1, 2, 1, 1, 1, 2, 1,
    2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
WORD_MULTIPLIER = [
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1,
    1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1,
    1, 1, 1, 1, 1, 1, 2, 1, 2, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1, 1,
    3, 1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 2, 1, 2, 1, 1, 1, 1, 1,
    1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1,
    1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    2, 1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 1, 1, 1]
TILE_FREQUENCY = {
    'a': 9, 'b': 2, 'c': 2, 'd': 4, 'e': 12, 'f': 2, 'g': 3, 'h': 2,
    'i': 9, 'j': 1, 'k': 1, 'l': 4, 'm': 2, 'n': 6, 'o': 8, 'p': 2,
    'q': 1, 'r': 6, 's': 4, 't': 6, 'u': 4, 'v': 2, 'w': 2, 'x': 1,
    'y': 2, 'z': 1, WILD: 2}
TILE_VALUE = {
    'a': 1, 'b': 5, 'c': 4, 'd': 3, 'e': 1, 'f': 5, 'g': 4, 'h': 4,
    'i': 1, 'j': 9, 'k': 6, 'l': 2, 'm': 4, 'n': 2, 'o': 1, 'p': 4,
    'q': 10, 'r': 2, 's': 1, 't': 1, 'u': 2, 'v': 5, 'w': 5, 'x': 8,
    'y': 5, 'z': 10, WILD: 0}


class Move(object):
    '''
    Movement information.
    '''

    def __init__(self, x, y, direction, tiles, score, words):
        self.x = x
        self.y = y
        self.direction = direction
        self.tiles = tiles
        self.score = score
        self.words = words

    def __str__(self):
        words = ', '.join(self.words)
        return '%d %s "%s" [%s]' % (
            self.score, self.vector, self.tiles, words)

    @property
    def key(self):
        return (-self.score, self.tiles)

    @property
    def vector(self):
        row = '%02d' % (self.y + 1)
        col = chr(ord('A') + self.x)
        if self.direction == HORIZONTAL:
            return row + col
        else:
            return col + row


class Board(object):
    '''
    Handling local board.
    '''

    def __init__(self):
        self.width = WIDTH
        self.height = HEIGHT
        self.start = START
        self.letter_multiplier = LETTER_MULTIPLIER
        self.word_multiplier = WORD_MULTIPLIER
        self.tile_value = TILE_VALUE
        self.tiles = [EMPTY] * BOARD_SIZE

    def __str__(self):
        width = self.width
        data = ''.join(self.tiles)
        rows = []
        for index in xrange(len(data) / width):
            rows.append(data[index * width:index * width + width])
        return '\n'.join(rows)

    def index(self, x, y):
        return y * self.width + x

    def get_tile(self, x, y):
        return self.tiles[self.index(x, y)]

    def is_empty(self, x, y):
        return self.get_tile(x, y) == EMPTY

    def is_adjacent(self, x, y):
        #if self.index(x, y) == self.start:
        #   return True
        if x > 0 and not self.is_empty(x - 1, y):
            return True
        if y > 0 and not self.is_empty(x, y - 1):
            return True
        if x < self.width - 2 and not self.is_empty(x + 1, y):
            return True
        if y < self.height - 2 and not self.is_empty(x, y + 1):
            return True
        return False

    def do_move(self, move):
        '''
        Execute the move on local board.
        '''
        x, y = move.x, move.y
        dx, dy = DIRECTION[move.direction]
        for tile in move.tiles:
            if tile != SKIP:
                index = self.index(x, y)
                self.tiles[index] = tile
            x += dx
            y += dy

    def undo_move(self, move):
        '''
        Undo local board move.
        '''
        x, y = move.x, move.y
        dx, dy = DIRECTION[move.direction]
        for tile in move.tiles:
            if tile != SKIP:
                index = self.index(x, y)
                self.tiles[index] = EMPTY
            x += dx
            y += dy

# Engine

def load_dawg(path):
    '''
    Load dawg file.
    '''
    with open(path, 'rb') as fp:
        data = fp.read()
    groups = {}
    start = 0
    lookup = {}
    for index in xrange(len(data) / 4):
        block = data[index * 4:index * 4 + 4]
        x = struct.unpack('<I', block)[0]
        link = x & 0xffffff
        letter = chr((x >> 24) & 0x7f)
        more = bool((x >> 31) & 1)
        lookup[letter] = link
        if not more:
            groups[start] = lookup
            start = index + 1
            lookup = {}
    for lookup in groups.itervalues():
        for letter, link in lookup.iteritems():
            lookup[letter] = groups[link] if link else None
    return groups[0]


def check_dawg(dawg, word):
    '''
    Check dawg for supplied word.
    '''
    word = '%s$' % word.lower()
    node = dawg
    for letter in word:
        if letter in node:
            node = node[letter]
        else:
            return False
    return True


def key_letter(tile):
    '''
    Pairing key and letter.
    '''
    if tile.isupper():
        key = WILD
        letter = tile.lower()
    else:
        key = tile
        letter = tile
    return (key, letter)


def compute_move(board, dawg, x, y, direction, tiles):
    '''
    Do movement computation.
    '''
    mx, my = x, y
    dx, dy = DIRECTION[direction]
    px, py = int(not dx), int(not dy)
    main_word = []
    main_score = 0
    sub_scores = 0
    multiplier = 1
    words = []
    placed = 0
    adjacent = False
    # check for dangling tiles before word
    ax, ay = x - dx, y - dy
    if ax >= 0 and ay >= 0 and board.get_tile(ax, ay) != EMPTY:
        return None
    for tile in tiles:
        # check for board run off
        if x < 0 or y < 0 or x >= board.width or y >= board.height:
            return None
        adjacent = adjacent or board.is_adjacent(x, y)
        index = board.index(x, y)
        if tile == SKIP:
            tile = board.get_tile(x, y)
            if tile == EMPTY:
                return None
            key, letter = key_letter(tile)
            main_word.append(letter)
            main_score += board.tile_value[key]
        else:
            placed += 1
            key, letter = key_letter(tile)
            main_word.append(letter)
            nx = (LEFT + x) % 14
            ny = (TOP + y) % 14
            original_index = ((y * 14) + x)
            bonus_index = ((ny * 14) + nx)
            main_score += board.tile_value[key] * \
                board.letter_multiplier[bonus_index]
            multiplier *= board.word_multiplier[bonus_index]
            # check for perpendicular word
            sub_word = [letter]
            sub_score = board.tile_value[key] * \
                board.letter_multiplier[bonus_index]
            n = 1
            while True: # prefix
                sx = x - px * n
                sy = y - py * n
                if sx < 0 or sy < 0:
                    break
                tile = board.get_tile(sx, sy)
                if tile == EMPTY:
                    break
                key, letter = key_letter(tile)
                sub_word.insert(0, letter)
                sub_score += board.tile_value[key]
                n += 1
            n = 1
            while True: # suffix
                sx = x + px * n
                sy = y + py * n
                if sx >= board.width or sy >= board.height:
                    break
                tile = board.get_tile(sx, sy)
                if tile == EMPTY:
                    break
                key, letter = key_letter(tile)
                sub_word.append(letter)
                sub_score += board.tile_value[key]
                n += 1
            if len(sub_word) > 1:
                #sub_score *= board.word_multiplier[index]
                sub_score *= board.word_multiplier[bonus_index]
                sub_scores += sub_score
                sub_word = ''.join(sub_word)
                words.append(str(sub_word))
        x += dx
        y += dy
    # check for dangling tiles after word
    if x < board.width and y < board.height and \
        board.get_tile(x, y) != EMPTY:
        return None
    # check for placed tiles
    if not adjacent:
        return None
    if placed < 1 or placed > RACK_SIZE:
        return None
    # compute score
    main_score *= multiplier
    score = main_score + sub_scores
    if placed == RACK_SIZE:
        score += BINGO
    main_word = ''.join(main_word)
    words.insert(0, str(main_word))
    # check words
    for word in words:
        if not check_dawg(dawg, word):
            return None
    # build result
    return Move(mx, my, direction, tiles, score, words)

def get_horizontal_starts(board, tile_count):
    '''
    Get horizontal starting point.
    '''
    result = [0] * (board.width * board.height)
    for y in xrange(board.height):
        for x in xrange(board.width):
            if x > 0 and not board.is_empty(x - 1, y):
                continue
            if board.is_empty(x, y):
                for i in xrange(tile_count):
                    if x + i < board.width and board.is_adjacent(x + i, y):
                        result[board.index(x, y)] = i + 1
                        break
            else:
                result[board.index(x, y)] = 1
    return result

def get_vertical_starts(board, tile_count):
    '''
    Get vertical starting point.
    '''
    result = [0] * (board.width * board.height)
    for y in xrange(board.height):
        for x in xrange(board.width):
            if y > 0 and not board.is_empty(x, y - 1):
                continue
            if board.is_empty(x, y):
                for i in xrange(tile_count):
                    if y + i < board.height and board.is_adjacent(x, y + i):
                        result[board.index(x, y)] = i + 1
                        break
            else:
                result[board.index(x, y)] = 1
    return result

def _generate(board, x, y, dx, dy, counts, node, tiles, min_tiles, results):
    '''
    Subprocess for generating movement candidates.
    '''
    if len(tiles) >= min_tiles and SENTINEL in node:
        results.append(''.join(tiles))
    if x >= board.width or y >= board.height:
        return
    tile = board.get_tile(x, y).lower()
    if tile == EMPTY:
        for tile in counts:
            if counts[tile]:
                if tile == WILD:
                    for letter in xrange(26):
                        tile = chr(ord('a') + letter)
                        if tile in node:
                            counts[WILD] -= 1
                            tiles.append(tile.upper())
                            _generate(board, x + dx, y + dy, dx, dy, counts,
                                node[tile], tiles, min_tiles, results)
                            tiles.pop()
                            counts[WILD] += 1
                else:
                    if tile in node:
                        counts[tile] -= 1
                        tiles.append(tile)
                        _generate(board, x + dx, y + dy, dx, dy, counts,
                            node[tile], tiles, min_tiles, results)
                        tiles.pop()
                        counts[tile] += 1
    else:
        if tile in node:
            tiles.append(SKIP)
            _generate(board, x + dx, y + dy, dx, dy, counts, node[tile],
                tiles, min_tiles, results)
            tiles.pop()

def generate(board, dawg, tiles):
    '''
    Generate movement candidates.
    '''
    moves = []
    tiles = [letter.lower() for letter in tiles]
    counts = dict((letter, tiles.count(letter)) for letter in set(tiles))
    hstarts = get_horizontal_starts(board, len(tiles))
    vstarts = get_vertical_starts(board, len(tiles))
    for y in xrange(board.height):
        for x in xrange(board.width):
            index = board.index(x, y)
            min_tiles = hstarts[index]
            if min_tiles:
                direction = HORIZONTAL
                dx, dy = DIRECTION[direction]
                results = []
                _generate(board, x, y, dx, dy, counts, dawg, [],
                    min_tiles, results)
                for result in results:
                    move = compute_move(
                        board, dawg, x, y, direction, result)
                    if move:
                        moves.append(move)
            min_tiles = vstarts[index]
            if min_tiles:
                direction = VERTICAL
                dx, dy = DIRECTION[direction]
                results = []
                _generate(board, x, y, dx, dy, counts, dawg, [],
                    min_tiles, results)
                for result in results:
                    move = compute_move(
                        board, dawg, x, y, direction, result)
                    if move:
                        moves.append(move)
    return moves

DAWG = load_dawg('files/twl.dawg')

def generate_moves(board, letters):
    return generate(board, DAWG, letters)


# Bot
class WordsquaredPlayer(object):

    def __init__(self, username, password):
        '''
        Boo-yah!
        '''
        self.username = USERNAME
        self.password = PASSWORD
        self.headers = {'User-Agent': USER_AGENT}
        self.cookies = {}
        self.authenticity_token = None
        self.request = self._get(WSQD)
        self.cookies = self.request.cookies
        pattern = re.compile('name="csrf-token" content="(.*?)"/>')
        self.authenticity_token = str(pattern.findall(self.request.text)[0])
        self.payload = {
            'utf8': '✓',
            'authenticity_token': self.authenticity_token,
            'user[username]': self.username,
            'user[password]': self.password,
            'user[remember_me]': 0}
        self.request = self._post('%s/users/sign_in' % WSQD,
            payload=self.payload)
        self.response = json.loads(self.request.text)
        self.game_id = str(self.response['gameId'])

    def _get(self, URL, payload=None):
        '''
        Simple wrapper for requests.get().
        '''
        self.payload = payload
        self.headers['Origin'] = WSQD
        self.headers['Referer'] = '%s/' % WSQD
        if self.authenticity_token:
            self.headers['X-CSRF-Token'] = self.authenticity_token
        self.headers['X-Requested-With'] = 'XMLHttpRequest'
        self.request = requests.get(
            URL, params=self.payload,
            headers=self.headers,
            cookies=self.cookies,
            #config=REQUESTS_CONFIG,
            timeout=TIMEOUT)
        self.cookies = self.request.cookies
        return self.request

    def _post(self, URL, payload=None):
        '''
        Simple wrapper for requests.post().
        '''
        self.payload = payload
        self.headers['Origin'] = WSQD
        self.headers['Referer'] = '%s/' % WSQD
        if self.authenticity_token:
            self.headers['X-CSRF-Token'] = self.authenticity_token
        self.headers['X-Requested-With'] = 'XMLHttpRequest'
        self.cookies['repeatCustomer'] = 'true'
        self.cookies['newsViewed'] = 'true'
        self.request = requests.post(
            URL,
            data=self.payload,
            headers=self.headers,
            cookies=self.cookies,
            #config=REQUESTS_CONFIG,
            timeout=TIMEOUT)
        self.cookies = self.request.cookies
        return self.request

    def load_game(self):
        '''
        Load game.
        '''
        self.payload = {'game': self.game_id}
        self.request = self._post('%s/v2/load_game' % WSQD,
            payload=self.payload)
        self.response = json.loads(self.request.text)
        self.shortlink = self.response['shortlink']
        self.last_move = self.response['user']['profile']['recent_words'][0]
        #self.last_move = self.response['user']['profile']['latest_tile_coords'][0]
        self.gx = self.last_move['coords'][0]['x']
        self.gy = self.last_move['coords'][0]['y']
        self.rack = self.response['assigned_letters']
        self.word_packs = []
        # XXX: requires word_packs
        #not_owned = self.response['user']['profile']['word_packs']['not_owned']
        #for word_id in not_owned:
        #    self.word_packs.extend(
        #        self.response['user']['profile']['word_packs']
        #        ['user_word_packs'][word_id]['words_remaining']
        #        .lower().split(', '))
        return {
            'gx': self.gx, 'gy': self.gy, 'rack': self.rack,
            'shortlink': self.shortlink, 'word_packs': self.word_packs}

    def tiles_for(self, gx=None, gy=None):
        '''
        Fetch the board.
        '''
        global LEFT
        global TOP
        self.gx = gx
        self.gy = gy
        self.left = (self.gx - MEDIAN_WIDTH)
        self.right = (self.gx + MEDIAN_WIDTH)
        self.top = (self.gy + MEDIAN_HEIGHT)
        self.bottom = (self.gy - MEDIAN_HEIGHT)
        TOP = (13 - (self.top % 14))
        LEFT = (self.left % 14)
        self.payload = {
            'game': self.game_id,
            'left': self.left,
            'right': self.right,
            'top': self.top,
            'bottom': self.bottom}
        self.request = self._get('%s/v2/tiles_for' % WSQD,
            payload=self.payload)
        self.response = json.loads(self.request.text)
        if self.response['result'] == 'success':
            self.board = Board()
            for tile in range(len(self.response['tiles'])):
                self.x = self.response['tiles'][tile]['x'] - self.left
                self.y = self.top - self.response['tiles'][tile]['y']
                self.letter = self.response['tiles'][tile]['letter']
                self.board.tiles[self.board.index(self.x, self.y)] = \
                    str(self.letter).lower()
            return self.board
        else:
            return None

    def drag(self, payload=None):
        '''
        Drag player tile to board.
        '''
        self.payload = payload
        self.payload['shortlink'] = self.shortlink
        request = self._post('%s/v2/drag' % WSQD, payload=payload)
        self.response = json.loads(self.request.text)
        if self.response['result'] == 'success':
            return True
        else:
            return False

    def play(self, payload=None):
        '''
        Submit word to board.
        '''
        self.payload = payload
        self.payload['game'] = self.game_id
        self.request = self._post('%s/v2/play' % WSQD, payload=self.payload)
        self.response = json.loads(self.request.text)
        self.status = self.response['result']
        if self.status == 'success':
            self.shortlink = self.response['shortlink']
            self.score = self.response['move_score']
            self.rack = self.response['assigned_letters']
            self.word_packs = []
            # XXX: requires word_packs
            #not_owned = self.response['user']['profile'] \
            #    ['word_packs']['not_owned']
            #for word_id in not_owned:
            #    self.word_packs.extend(
            #        self.response['user']['profile']['word_packs']
            #        ['user_word_packs'][word_id]['words_remaining']
            #        .lower().split(', '))
            return {
                'status': self.status,
                'score': self.score,
                'rack': self.rack,
                'word_packs': self.word_packs}
        else:
            self.message = self.response['message']
            return {'status': self.status, 'message': self.message}

    def swap_rack(self):
        '''
        Swap rack.
        '''
        self.payload = {'game': self.game_id}
        self.request = self._post('%s/v2/swap_rack' % WSQD,
            payload=self.payload)
        self.response = json.loads(self.request.text)
        return self.response

    def location_shift(self, gx=None, gy=None):
        '''
        Shift to new location when the automated play is stuck.
        '''
        self.gx = gx
        self.gy = gy
        self.area = {}
        self.area['NW'] = {
            'gx': self.gx - MEDIAN_WIDTH,
            'gy': self.gy + MEDIAN_HEIGHT}
        self.area['SW'] = {
            'gx': self.gx - MEDIAN_WIDTH,
            'gy': self.gy - MEDIAN_HEIGHT}
        self.area['NE'] = {
            'gx': self.gx + MEDIAN_WIDTH,
            'gy': self.gy + MEDIAN_HEIGHT}
        self.area['SE'] = {
            'gx': self.gx + MEDIAN_WIDTH,
            'gy': self.gy - MEDIAN_HEIGHT}
        self.area['N'] = {
            'gx': self.gx,
            'gy': self.gy + MEDIAN_HEIGHT}
        self.area['S'] = {
            'gx': self.gx,
            'gy': self.gy - MEDIAN_HEIGHT}
        self.area['W'] = {
            'gx': self.gx - MEDIAN_WIDTH,
            'gy': self.gy}
        self.area['E'] = {
            'gx': self.gx + MEDIAN_WIDTH,
            'gy': self.gy}
        for location in ['NW', 'SW', 'NE', 'SE', 'N', 'S', 'W', 'E']:
            self.area[location][EMPTY] = collections.Counter(
                self.tiles_for(
                    gx=self.area[location]['gx'],
                    gy=self.area[location]['gy']).tiles)[EMPTY]
        self.area = sorted(
            self.area.iteritems(),
            key=operator.itemgetter(1),
            reverse=True)
        # Sample:
        # self.area = [('NE', {'.': 165, 'gx': 15, 'gy': 15}),
        #              ('SW', {'.': 107, 'gx': 5, 'gy': 5}),
        #         ...
        # XXX: Exclude the area[0], sometime it's just an empty area.
        self.random_area = random.choice(self.area[0:5])
        return (
            self.random_area[0],
            self.random_area[1]['gx'],
            self.random_area[1]['gy'])


class GiveMeABreak(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


if __name__ == '__main__':
    STUCK = 0
    FALLBACK = False
    CROWDED = False
    MAX_FILLED = BOARD_SIZE - (BOARD_SIZE/2)
    WALKS = 0
    MAX_WALKS = ODD_NUMBER * 2

    # Login
    bot = WordsquaredPlayer(USERNAME, PASSWORD)
    logger.debug('Logged in as "%s".' % USERNAME)

    # Load game
    load_game = bot.load_game()
    rack = load_game['rack']
    shortlink = load_game['shortlink']
    gx = load_game['gx']
    gy = load_game['gy']
    word_packs = load_game['word_packs']

    # Load board
    board = bot.tiles_for(gx=gx, gy=gy)

    LOOKING_FOR_LONG_WORDS = True
    LONG_WORDS_ERROR = False
    WORD_PACKS_ERROR = False

    while True:
        try:
            if CROWDED or FALLBACK:
                CROWDED = False
                if FALLBACK:
                    load_game = bot.load_game()
                    rack = load_game['rack']
                    shortlink = load_game['shortlink']
                    gx = load_game['gx']
                    gy = load_game['gy']
                    word_packs = load_game['word_packs']
                    logger.debug('Fallback.')
                (location, gx, gy) = bot.location_shift(gx=gx, gy=gy)
                START = LOCATION_START[location]
                #time.sleep(1)
                board = bot.tiles_for(gx=gx, gy=gy)
                error_coords = []
                logger.debug('Moving to %s (%d, %d).' % (location, gx, gy))

                # Apparently, there's no need to swap the rack.
                # Will keep this for historical reason.
                #rack = bot.swap_rack()['assigned_letters']
                #logger.debug('Got stuck. Swap the rack.')

            # Don't be too greedy
            #time.sleep(3)
            #board = bot.tiles_for(gx=gx, gy=gy)

            area_empty = collections.Counter(board.tiles)[EMPTY]
            area_filled = len(board.tiles) - area_empty
            
            if area_filled >= MAX_FILLED or WALKS >= MAX_WALKS:
                CROWDED = True
                raise GiveMeABreak(
                    'Too crowded or maximum walks reached.'
                    ' Empty: %d, Limit: %d, Total: %d.' % \
                        (area_empty, MAX_FILLED, len(board.tiles)))

            # Lazy hack to get seven letters of O, I, T, A, E
            #rack = [letter.upper() for letter in rack]
            #if ''.join(set(rack)) == 'E':
            #    logger.debug('You have seven %s in your rack' % rack[0])
            #    sys.exit(1)
            #for i in xrange(len(rack)):
            #    if 'E' in rack:
            #        rack.remove('E')

            moves = generate_moves(board,
                [letter.lower() for letter in rack])
            len_moves = len(moves)

            if not len_moves:
                FALLBACK = True
                raise GiveMeABreak('Zero move.')

            # find word in word packs or long words
            if word_packs or LOOKING_FOR_LONG_WORDS:
                word_packs_moves = []
                long_words_moves = []
                for i in xrange(len_moves):
                    for word in moves[i].words:
                        if len(word) >= 14:
                            long_words_moves.append(moves[i])
                        if word in word_packs:
                            word_packs_moves.append(moves[i])
                if long_words_moves and not LONG_WORDS_ERROR:
                    moves = long_words_moves
                    moves.sort(key=lambda x: x.key)
                    logger.debug('Found some long words.')
                if word_packs_moves and not WORD_PACKS_ERROR:
                    moves = word_packs_moves
                    moves.sort(key=lambda x: x.key)
                    logger.debug('Found some words from word packs.')

            moves.sort(key=lambda x: x.key)
            logger.debug(
                'Working on (%d, %d).'
                ' There are %d possible %s.'
                ' Current rack: %s.' % (
                    gx, gy, len_moves, 'moves' if len_moves >= 2 else 'move',
                    ''.join(rack)))

            for i in xrange(len_moves):
                move = moves[i]
                left = (gx - MEDIAN_WIDTH)
                top = (gy + MEDIAN_HEIGHT)
                coordinate = {'x': left + move.x, 'y': top - move.y}
                (cx, cy) = (coordinate['x'], coordinate['y'])
                (dx, dy) = DIRECTION[move.direction]

                seq = 0
                cancel_drag = []
                dict_play = {}
                dict_drag = {}

                for num in xrange(len(move.tiles)):
                    if move.tiles[num] != SKIP:
                        if DEBUG and DEBUG_LEVEL >= 3:
                            logger.debug('Placing: %s on (%d, %d)' % (
                                move.tiles[num].upper(), cx, cy))
                        dict_play['tiles[%d][letter]' % seq] = \
                            move.tiles[num].upper()
                        dict_play['tiles[%d][wildcard]' % seq] = 'false'
                        dict_play['tiles[%d][x]' % seq] = cx
                        dict_play['tiles[%d][y]' % seq] = cy
                        dict_drag['added[]'] = '%d,%d' % (cx, cy)
                        cancel_drag.append((cx, cy))
                        seq += 1
                        bot.drag(payload=dict_drag)
                    cx += dx
                    cy -= dy
                play = bot.play(payload=dict_play)

                if play['status'] == 'success':
                    board.do_move(move)
                    STUCK = 0
                    FALLBACK = False
                    WORD_PACKS_ERROR = False
                    LONG_WORDS_ERROR = False
                    WALKS += 1

                    rack = play['rack']
                    word_packs = play['word_packs']
                    logger.info(
                        '(%d, %d) "%s" %s - Direction: %s - Score: %s.' % (
                            coordinate['x'], coordinate['y'],
                            move.tiles, move.words,
                            'HORIZONTAL' if move.direction == 1 else \
                                'VERTICAL',
                            play['score']))
                    break
                else:
                    board.undo_move(move)
                    word_packs_error = []
                    long_words_error = []

                    for word in move.words:
                        if len(word) >= 14:
                            long_words_error.append(word)
                            LONG_WORDS_ERROR = True
                        if word in word_packs:
                            word_packs_error.append(word)
                            WORD_PACKS_ERROR = True
                    logger.error(
                        '(%d, %d) "%s" %s - %s' % (
                            coordinate['x'], coordinate['y'],
                            move.tiles, move.words, play['message']))

                    # Cancel the tiles drag
                    for c in cancel_drag:
                        dict_drag = {}
                        dict_drag['removed[]'] = '%s,%s' % (c[0], c[1])
                        bot.drag(payload=dict_drag)

                    # XXX: If we're going too far, fall back to the last
                    #      success move.
                    # - You must play your tiles next to at least one
                    #   existing tile
                    if 'must play' in play['message']:
                        # Placed the tiles on empty area. Not accepted.
                        FALLBACK = True
                        STUCK += 1

                    # - You tried to place a tile where one already exists.
                    if 'already exists' in play['message']:
                        # There's another player on the same area
                        # Reload the board
                        board = bot.tiles_for(gx=gx, gy=gy)
                        STUCK += 1

                    # The following errors are ignored. Will keep trying until
                    # reaching the limit.
                    # - You must build off of your own words (non-gray tiles)
                    #   after your first turn
                    # - WORD is not a valid word
                    # - 0 move.
                    if 'non-gray' in play['message'] or \
                        'not a valid word' in play['message']:
                        STUCK += 1

                    if STUCK >= ODD_NUMBER:
                        FALLBACK = True
                        break

        except KeyboardInterrupt:
            sys.exit(1)
        except EOFError:
            sys.exit(1)
        except GiveMeABreak as e:
            logger.error(e)
        except Exception, e:
            logger.error(e)
            if DEBUG and DEBUG_LEVEL >= 2:
                traceback.print_exc()
                sys.exit(1)
            else:
                FALLBACK = True
                time.sleep(10)
