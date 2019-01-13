#!/usr/bin/env python3
# Python 3.6
# halite.exe --replay-directory replays/ -vvv --width 32 --height 32 "python MyBot20.py" "python MyBot.py"
import hlt
from hlt import constants
from hlt.positionals import Direction, Position
import logging
import numpy as np


def normalize_directional_offset(m):
    return game_map.normalize(ship.position.directional_offset(m))


def directional(position):
    for direction in game_map.get_unsafe_moves(ship.position, position):
        target_position = normalize_directional_offset(direction)
        if target_position not in next_positions_list and target_position not in enemy_ships:
            m = direction
            return m
    return


def save_move():
    for position in ship.position.get_surrounding_cardinals():
        if position not in next_positions_list and position not in enemy_ships:
            m = game_map.get_unsafe_moves(ship.position, position)[0]
            return m
    return


def target_max_halite(n=1):
    for position in all_positions:
        target_position = Position(*position)
        target_distance = game_map.calculate_distance(ship.position, target_position)
        if target_position not in target_position_dict.values():
            if target_distance < MAP_SIZE // n and game_map[target_position].halite_amount > HALITE_LIMIT:
                m = directional(target_position)
                if m is not None:
                    target_position_dict[ship.id] = target_position
                    all_positions.remove(position)
                    return m
    return


def halite_scan(radius):
    halite = 0
    for position in get_search_radius(radius):
        halite += game_map[position].halite_amount
    return halite


def get_search_radius(radius):
    """ returns a list of all positions within square radius of a ship """
    return [ship.position+Position(i, j) for i in range(-radius, radius+1) for j in range(-radius, radius+1)]


game = hlt.Game()
game.ready("ZalmarBot v21")

MAX_TURNS = constants.MAX_TURNS
TURNS_LIMIT = constants.MAX_TURNS * 0.65
MAP_SIZE = game.game_map.height
SHIPS_LIMIT = MAP_SIZE * 1.4
HALITE_LIMIT = constants.MAX_HALITE * 0.05
COLLECTION_LIMIT = constants.MAX_HALITE * 0.95
DROPOFF_COUNT = 0
dropoff_position = Position(0, 0)

if MAP_SIZE < 48:
    TURNS_LIMIT = constants.MAX_TURNS * 0.5
    SHIPS_LIMIT = MAP_SIZE

logging.info(f'Successfully created bot! My Player ID is {game.my_id}.')
logging.info(f'Max turns is {MAX_TURNS}. Map size is {MAP_SIZE}x{MAP_SIZE}.')

ship_status = {}

target_position_dict = {}

while True:
    game.update_frame()
    me = game.me
    game_map = game.game_map

    command_queue = []

    map_positions = [(y, x) for x in range(MAP_SIZE) for y in range(MAP_SIZE)]
    all_positions_dict = {position: game.game_map[Position(*position)].halite_amount for position in map_positions}
    all_positions = sorted(all_positions_dict, key=all_positions_dict.get, reverse=True)

    mean_halite_on_map = np.mean(list(all_positions_dict.values()))
    if mean_halite_on_map < HALITE_LIMIT:
        HALITE_LIMIT = mean_halite_on_map / 2

    next_positions_list = [ship.position for ship in me.get_ships()
                           if ship.halite_amount < game_map[ship.position].halite_amount * 0.10
                           or game_map[ship.position].halite_amount > HALITE_LIMIT]

    """Check enemy ships"""
    players_list = [player for id_, player in game.players.items() if id_ != me.id]
    enemy_ships = []
    for player in players_list:
        enemy_ships += [Position(*(ship.position.x, ship.position.y)) for ship in player.get_ships()]
    # for pos in enemy_ships:
    #     for p in pos.get_surrounding_cardinals():
    #         if game_map[p].halite_amount > game_map[pos].halite_amount:
    #             enemy_ships.append(p)
    # logging.info(f'enemy_ships {enemy_ships}')

    """Ship spawn"""
    if len(me.get_ships()) < MAP_SIZE and DROPOFF_COUNT < 1:
        ship_spawn = True
    elif DROPOFF_COUNT >= 1:
        ship_spawn = True
    else:
        ship_spawn = False

    if game.turn_number <= TURNS_LIMIT and ship_spawn and len(me.get_ships()) < SHIPS_LIMIT:
        if me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
            command_queue.append(me.shipyard.spawn())
            next_positions_list.append(me.shipyard.position)

    last_turn = constants.MAX_TURNS - game.turn_number

    max_distance_to_home = 0
    max_distance_to_dropoff = 0

    if len(me.get_ships()) > 0:
        max_distance_to_home = max([
            game_map.calculate_distance(ship.position, me.shipyard.position) for ship in me.get_ships()])
        max_distance_to_dropoff = max(
            [game_map.calculate_distance(ship.position, dropoff_position) for ship in me.get_ships()])

    for ship in me.get_ships():
        if last_turn < max_distance_to_home // 1.2 or last_turn < max_distance_to_dropoff // 1.2:
            distance_to_home = game_map.calculate_distance(ship.position, me.shipyard.position)
            distance_to_dropoff = game_map.calculate_distance(ship.position, dropoff_position)
            if distance_to_home > distance_to_dropoff:
                if distance_to_dropoff == 1:
                    command_queue.append(ship.move(game_map.get_unsafe_moves(ship.position, dropoff_position)[0]))
                    continue
                else:
                    command_queue.append(ship.move(game_map.naive_navigate(ship, dropoff_position)))
                    continue
            else:
                if distance_to_home == 1:
                    command_queue.append(ship.move(game_map.get_unsafe_moves(ship.position, me.shipyard.position)[0]))
                    continue
                else:
                    command_queue.append(ship.move(game_map.naive_navigate(ship, me.shipyard.position)))
                    continue

        if ship.id not in ship_status:
            ship_status[ship.id] = "exploring"

        if ship_status[ship.id] == "returning":
            if ship.position == me.shipyard.position or ship.position == dropoff_position:
                ship_status[ship.id] = "exploring"

        elif ship.halite_amount >= COLLECTION_LIMIT:
            ship_status[ship.id] = "returning"

        if DROPOFF_COUNT < 1:
            if game_map.calculate_distance(ship.position, me.shipyard.position) > MAP_SIZE / 2.5:
                if halite_scan(5) > 14000 and me.halite_amount > constants.DROPOFF_COST:
                    dropoff_position = ship.position
                    DROPOFF_COUNT += 1
                    command_queue.append(ship.make_dropoff())
                    continue

        move = None
        flag_move = False
        next_position = None

        if ship.halite_amount >= game_map[ship.position].halite_amount * 0.10:
            flag_move = True
        else:
            flag_move = False

        if game_map[ship.position].halite_amount > HALITE_LIMIT and not ship.is_full:
            flag_move = False

        if flag_move:
            if move is None:
                if (ship.id in target_position_dict
                        and target_position_dict[ship.id] != ship.position
                        and game_map[target_position_dict[ship.id]].halite_amount > HALITE_LIMIT):
                    move = directional(target_position_dict[ship.id])
                else:
                    move = target_max_halite(12)

            if move is None:
                if (ship.id in target_position_dict
                        and target_position_dict[ship.id] != ship.position
                        and game_map[target_position_dict[ship.id]].halite_amount > HALITE_LIMIT):
                    move = directional(target_position_dict[ship.id])
                else:
                    move = target_max_halite(6)

            if move is None:
                if (ship.id in target_position_dict
                        and target_position_dict[ship.id] != ship.position
                        and game_map[target_position_dict[ship.id]].halite_amount > HALITE_LIMIT):
                    move = directional(target_position_dict[ship.id])
                else:
                    move = target_max_halite(3)

            if move is None:
                if (ship.id in target_position_dict
                        and target_position_dict[ship.id] != ship.position
                        and game_map[target_position_dict[ship.id]].halite_amount > HALITE_LIMIT):
                    move = directional(target_position_dict[ship.id])
                else:
                    move = target_max_halite()

            if move is None:
                move = save_move()
                if move is None:
                    move = Direction.Still
        else:
            move = Direction.Still
            next_position = ship.position

        if ship_status[ship.id] == "returning":
            if DROPOFF_COUNT > 0:
                distance_to_home = game_map.calculate_distance(ship.position, me.shipyard.position)
                distance_to_dropoff = game_map.calculate_distance(ship.position, dropoff_position)
                if distance_to_home < distance_to_dropoff:
                    move = directional(me.shipyard.position)
                else:
                    move = directional(dropoff_position)
                if move is None:
                    move = save_move()
                    if move is None:
                        move = Direction.Still
            else:
                move = directional(me.shipyard.position)
                if move is None:
                    move = save_move()
                    if move is None:
                        move = Direction.Still

        next_position = normalize_directional_offset(move)

        if next_position != ship.position:
            next_positions_list = list(set(next_positions_list))
            next_positions_list.append(next_position)

        command_queue.append(ship.move(move))

        logging.info(f'#{ship.id} {ship.position} Next -> {next_position} move -> {move} is {flag_move}')

    game.end_turn(command_queue)
