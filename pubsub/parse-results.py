__author__ = 'yuguang'

import csv, pprint

settings = {}
with open('results.csv', 'rb') as csvfile:
    results = csv.reader(csvfile)
    for row in results:
        if not ','.join(row[0:2]) in settings:
            settings[','.join(row[0:2])] = {
                'updates': 0,
                'jobs': 0,
                'errors': 0,
            }
        settings[','.join(row[0:2])]['updates'] += int(row[2])
        settings[','.join(row[0:2])]['jobs'] += int(row[3])
        settings[','.join(row[0:2])]['errors'] += int(row[4])

with open('consolidated-results.csv', 'wb') as file:
    for key, stats in settings.iteritems():
        file.write(','.join(map(str, [key, stats['updates'], stats['jobs'], stats['errors']]))  + '\n')