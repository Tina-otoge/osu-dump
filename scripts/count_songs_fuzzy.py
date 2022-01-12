from argparse import ArgumentParser
from datetime import datetime, timedelta
import json
import statistics


parser = ArgumentParser()
parser.add_argument('file', nargs='?', default='result.json')
args = parser.parse_args()

with open(args.file) as f:
    data = json.load(f)

data_total = len(data)

print('Normalizing keys, removing compilations')
REMOVE_CHARS = '[]()|:;\'"@,.+=!'
TRANS_TABLE = str.maketrans(
    REMOVE_CHARS,
    ' ' * len(REMOVE_CHARS)
)
def normalize(x: str):
    x = x.lower()
    x = x.translate(TRANS_TABLE)
    x = x.strip()
    return x

for x in data:
    for key in ('artist', 'title'):
        x[key] = normalize(x[key])

def detect_groups(x: dict):
    if x['artist'].startswith('various'):
        return False
    for word in ('compilation', 'training'):
        if word in x['title']:
            return False
    return True

def detect_empty_tags(x: dict):
    if not x['artist'] or not x['title']:
        return False
    return True

data = list(filter(detect_groups, data))

without_groups_total = len(data)

data = list(filter(detect_empty_tags, data))

without_empty_total = len(data)

print('Re-ordering by "artist" - "title", eliminating strict duplicates')
data_by_computed_name = {
    f"{x['artist'].lower()} - {x['title'].lower()}"
    for x in data
}

computed_total = len(data_by_computed_name)

print('Total entries', data_total)
print('Without compilations', without_groups_total)
print('Without empty tags', without_empty_total)
print('Unique entries', computed_total, f'({computed_total / data_total * 100}%)')
print('-' * 10, flush=True)

computed_by_letter = {}
for x in data_by_computed_name:
    letter = x[0]
    if letter not in computed_by_letter:
        computed_by_letter[letter] = []
    computed_by_letter[letter].append(x)

from thefuzz import process
last_run = datetime.now()
deltas = []
PRECISION = 95
count = 0
counted = 0
for letter in sorted(computed_by_letter.keys()):
    letter_data = computed_by_letter[letter]
    letter_data_total = len(letter_data)
    print('Handling entries starting with', f'"{letter}"', flush=True)
    for i, entry in enumerate(letter_data):
        if i % 100 == 0:
            now = datetime.now()
            if counted:
                delta = now - last_run
                delta = delta.total_seconds()
                deltas.append(delta)
                if len(deltas) > 20:
                    deltas.pop()
                mean = statistics.mean(deltas)
                print('Now', now)
                print('Mean', mean)
                print('ETA', timedelta(seconds=mean * (computed_total - counted)))
            print('Done with this letter', f'{i} / {letter_data_total}')
            print('Done total', f'{counted} / {computed_total}', f'{counted / computed_total * 100}%')
            if counted:
                print('Current unique count', f'{count} / {counted}', f'{count / counted * 100}%')
            print('-' * 10, flush=True)
        counted += 1
        count += 2
        results = process.extract(entry, letter_data, limit=10)
        dupes = list(filter(lambda x: x[1] >= PRECISION, results))
        if len(dupes) > 1:
            print('Dupes found:', dupes)
        count -= len(dupes)

print('Total without similars', count)

with open('result_total_without_similars.txt', 'w') as f:
    f.write(str(count))
