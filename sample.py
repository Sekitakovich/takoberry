import json

body = {
    'lat': 1.2,
    'lng': 3.4,
    'spd': 60,
}

pack = []

for a in range(5):
    pack.append(body)

print(json.dumps(pack))
