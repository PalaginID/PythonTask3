#!/bin/bash

locust -f ./locust.py --headless -u 100 -r 10 -t 1m --host http://app:8000