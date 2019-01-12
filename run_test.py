import json
import subprocess

bot0 = "MyBot20.py"
bot1 = "MyBot.py"


def run(size, game_count):
    win0 = 0
    win1 = 0
    for i in range(game_count):
        command = (f"./halite.exe --replay-directory replays/ -vvv --width "
                   f"{size} --height {size} --seed 1234567 --results-as-json".split())

        command.append(f'python {bot0}')
        command.append(f'python {bot1}')

        results = subprocess.check_output(command)
        results = json.loads(results)

        rank0 = results['stats']['0']['rank']
        rank1 = results['stats']['1']['rank']
        score0 = results['stats']['0']['score']
        score1 = results['stats']['1']['score']
        print(f'{bot0}: rank: {rank0} score: {score0} | {bot1}: rank: {rank1} score: {score1}')
        if rank0 == 1:
            win0 += 1
        else:
            win1 += 1

    if win0 > win1:
        print('-' * 75)
        print(f'Map size is {size}x{size} | Score {bot0} {win0}:{win1} {bot1} ---> WIN {bot0}')
        print('-' * 75)
    elif win0 < win1:
        print('-' * 75)
        print(f'Map size is {size}x{size} | Score {bot0} {win0}:{win1} {bot1} ---> WIN {bot1}')
        print('-' * 75)
    else:
        print('-' * 75)
        print(f'Map size is {size}x{size} | Score {bot0} {win0}:{win1} {bot1} ---> DRAW')
        print('-' * 75)


count = 1
run(32, count)
run(40, count)
run(48, count)
run(56, count)
run(64, count)
