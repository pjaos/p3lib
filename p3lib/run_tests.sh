#!/bin/sh
python3 uio_test.py
python3 -m pytest  test_json_networking.py
python3 -m pytest -s test_netif.py