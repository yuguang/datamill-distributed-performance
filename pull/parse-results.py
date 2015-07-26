__author__ = 'yuguang'

import csv, pprint

settings = {}
with open('results.csv', 'rb') as csvfile:
    results = csv.reader(csvfile)
    for row in results:
        if not ','.join(row[0:4]) in settings:
            settings[','.join(row[0:4])] = {
                'updates': 0,
                'jobs': 0,
                'errors': 0,
            }
        settings[','.join(row[0:4])]['updates'] += int(row[4])
        settings[','.join(row[0:4])]['jobs'] += int(row[5])
        settings[','.join(row[0:4])]['errors'] += int(row[6])

with open('consolidated-results.csv', 'wb') as file:
    for key, stats in settings.iteritems():
        file.write(','.join(map(str, [key, stats['updates'], stats['jobs'], stats['errors']]))  + '\n')