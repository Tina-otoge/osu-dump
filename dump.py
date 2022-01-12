from datetime import datetime, timedelta
import json
import os
import time
import statistics
import requests

result_path = 'result.json'
base = 'https://osu.ppy.sh/api/v2'
token = os.environ.get('TOKEN')
cursor = {}
total_done = 0
last_deltas = []
start = datetime.now()
last_run = start

with open(result_path, 'w') as f:
    f.write('[\n')

while True:
    resp = requests.get(
        f'{base}/beatmapsets/search/',
        headers={'Authorization': f'Bearer {token}'},
        params={
            'nsfw': 'true',
            'sort': 'title_asc',
            's': 'any',
            'cursor[_id]': cursor.get('_id'),
            'cursor[title.raw]': cursor.get('title.raw'),
        },
    )
    print(resp.request, resp.request.url)
    data = resp.json()
    with open('last_raw_response.json', 'w') as f:
        json.dump(data, f, indent=2)

    cursor = data['cursor']
    sets = data['beatmapsets']
    total = data['total']

    songs = [
        {
            'id': x['id'],
            'title': x['title'],
            'artist': x['artist'],
            'status': x['status'],
            'mapper_id': x['user_id'],

        } for x in sets
    ]
    total_done += len(songs)

    with open(result_path, 'a') as f:
        f.write(',\n'.join(json.dumps(x) for x in songs))

    now = datetime.now()
    last_deltas.append((now - last_run).total_seconds())
    last_run = now
    if len(last_deltas) > 20:
        last_deltas.pop()
    mean = statistics.mean(last_deltas)
    print('Now', now)
    print('Mean', mean)
    print('ETA', timedelta(seconds=mean * (total - total_done) / 50))
    print(f'{total_done} / {total}')


    time.sleep(0.5)

    # if len(songs) < 50 or total_done > 200:
    if len(songs) == 0:
        break

    with open(result_path, 'a') as f:
        f.write(',\n')

    print('-' * 10)

with open(result_path, 'a') as f:
    f.write('\n]')
