import csv
import os
import time

class CSVFeed:

    def __init__(self, file_path, transmit_rate):
        self._path = file_path
        self._transmit_rate = transmit_rate
        self._headers = []
        self._rows = []
    

    def load_file(self):
        with open(self.file_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')           
            for row in csv_reader:
                self._rows.append(row)

    def __call__(self):
        i = 0
        while True:
            for j, header in enumerate(self._headers):
                yield {'topic': header, 'body': float(self._rows[i][j])}

                i = i + 1 if i < len(self._rows) - 1 else 0
                time.sleep(self._transmit_rate)
