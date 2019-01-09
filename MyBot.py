#!/usr/bin/env python3
# Python 3.6
# halite.exe --replay-directory replays/ -vvv --width 32 --height 32 "python MyBot.py" "python MyBot.py"
import hlt
from hlt import constants
from hlt.positionals import Direction, Position
import logging
import random


def directional(position):
    """return next pos"""
    for direction in game_map.get_unsafe_moves(ship.position, position):
        target_position = ship.position.directional_offset(direction)
        if target_position not in next_positions_list:
            move = direction
            return move
    return


def save_move():
    for pos in ship.position.get_surrounding_cardinals():
        if pos not in next_positions_list:
            move = game_map.get_unsafe_moves(ship.position, pos)[0]
            return move
    return


game = hlt.Game()
game.ready("ZalmarBot v17")

MAX_TURNS = constants.MAX_TURNS
TURNS_LIMIT = constants.MAX_TURNS // 1.9
MAP_SIZE = game.game_map.height
SHIPS_LIMIT = MAP_SIZE * 1.25
HALITE_LIMIT = constants.MAX_HALITE * 0.03
COLLECTION_LIMIT = constants.MAX_HALITE * 0.95

logging.info(f'Successfully created bot! My Player ID is {game.my_id}.')
logging.info(f'Max turns is {MAX_TURNS}. Map size is {MAP_SIZE}x{MAP_SIZE}.')

ship_status = {}

while True:
    game.update_frame()
    me = game.me
    game_map = game.game_map

    command_queue = []

    map_positions = [(y, x) for x in range(MAP_SIZE) for y in range(MAP_SIZE)]
    all_positions = {position: game.game_map[Position(*position)].halite_amount for position in map_positions}
    all_positions = sorted(all_positions, key=all_positions.get, reverse=True)

    next_positions_list = [ship.position for ship in me.get_ships()]

    """Spawn ship"""
    if game.turn_number <= TURNS_LIMIT and len(me.get_ships()) < SHIPS_LIMIT:
        if me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
            command_queue.append(me.shipyard.spawn())
            next_positions_list.append(me.shipyard.position)

    for ship in me.get_ships():
        if ship.id not in ship_status:
            ship_status[ship.id] = "exploring"

        if ship_status[ship.id] == "returning":
            if ship.position == me.shipyard.position:
                ship_status[ship.id] = "exploring"
            else:

                move = directional(me.shipyard.position)

                if move is None:
                    move = save_move()
                    if move is None:
                        move = Direction.Still

                next_position = ship.position.directional_offset(move)

                if next_position != ship.position:
                    next_positions_list = list(set(next_positions_list))
                    next_positions_list.remove(ship.position)
                    next_positions_list.append(next_position)

                command_queue.append(ship.move(move))
                logging.info(f'#{ship.id} {ship.position} Next -> {next_position} move -> {move}')
                continue

        elif ship.halite_amount >= COLLECTION_LIMIT:
            ship_status[ship.id] = "returning"

        move = None
        flag_move = False
        next_position = None

        if ship.halite_amount >= game_map[ship.position].halite_amount * 0.10:
            flag_move = True
        else:
            flag_move = False

        if game_map[ship.position].halite_amount >= HALITE_LIMIT and ship_status[ship.id] == "exploring":
            flag_move = False

        if flag_move:
            max_halite = 0
            for position in ship.position.get_surrounding_cardinals():
                if game_map[position].halite_amount > max_halite:
                    next_position = position
                    max_halite = game_map[position].halite_amount

            if next_position is not None and next_position not in next_positions_list:
                move = game_map.get_unsafe_moves(ship.position, next_position)[0]
            else:
                move = save_move()
                if move is None:
                    move = Direction.Still

                next_position = ship.position.directional_offset(move)
        else:
            move = Direction.Still
            next_position = ship.position

        if next_position != ship.position:
            next_positions_list = list(set(next_positions_list))
            next_positions_list.remove(ship.position)
            next_positions_list.append(next_position)

        command_queue.append(ship.move(move))

        logging.info(f'#{ship.id} {ship.position} Next -> {next_position} move -> {move} is {flag_move}')

    game.end_turn(command_queue)

    logging.info(f'Next list pos {next_positions_list}')
