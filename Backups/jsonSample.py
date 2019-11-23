import json

response = [
    {
        'id': 1,
        'date': '2019-01-24',
        'time': '10:22:30.888888',
        'nmea': '!AIVDM,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,',
    },
    {
        'id': 2,
        'date': '2019-01-24',
        'time': '10:22:30.888888',
        'nmea': '!AIVDM,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,',
    },
]

empty = []

print(response)

t = json.dumps(response, indent=2)
print(t)

t = json.dumps(empty, indent=2)
print(t)
