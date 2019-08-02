#!/usr/bin/env python3

import json
import sys

input_file = sys.argv(1)
name, extension = input_file.split('.')
output_file = '.'.join([name + '_sorted', extension])

with open(input_file) as f:
    parsed = json.load(f)
    sorted_json = sorted(parsed, key=lambda x: x['time'])

with open(output_file, 'w') as fw:
    json.dump(sorted_json, fw)

