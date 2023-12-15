#!/bin/sh

export PATH=$PATH:.

python3 -m pipenv run bokeh_auth_test.py
python3.8 -m pipenv run uio_test.py
python3.8 -m pipenv run python -m pytest  test_json_networking.py
python3.8 -m pipenv run python -m pytest -s test_netif.py
python3.8 -m pipenv run python -m pytest -s test_ssh.py
python3.8 -m pipenv run python -m pytest -s test_conduit.py
echo "Open browser and display static graphs using plotly."
python3.8 -m pipenv run netplotly_demo
echo "Open browser and show real time plots using bokeh."
python3.8 -m pipenv run time_series_plot_example
# Other bokeh examples
# ./run_bokeh_demo.sh 
# python3.8 -m pipenv run python3 GUIModel_A_example.py