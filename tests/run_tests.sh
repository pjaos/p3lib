#!/bin/sh

export PATH=$PATH:.

pipenv run uio_test.py
pipenv run python -m pytest  test_json_networking.py
pipenv run python -m pytest -s test_netif.py
echo "Open browser and display static graphs using plotly."
pipenv run netplotly_demo
echo "Open browser and show real time plots using bokeh."
pipenv run time_series_plot_example