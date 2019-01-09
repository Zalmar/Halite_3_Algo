import json
import subprocess


win0 = 0
win1 = 0
bot0 = "MyBot.py"
bot1 = "MyBot.py"
size = 40
for i in range(9):
    command = f"./halite.exe --replay-directory replays/ -vvv --width {size} --height {size} --results-as-json".split()

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
    print(f'{bot0} {win0}:{win1} {bot1} \nWIN {bot0}')
else:
    print(f'{bot0} {win0}:{win1} {bot1} \nWIN {bot1}')
