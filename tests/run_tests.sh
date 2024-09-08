#!/bin/sh

export PATH=$PATH:.

# Uncomment this to build the python env. You probably want to do this outside this
# scripts as it takes some time and should only need to be done once.
# ./create_python_env.sh

python3 -m poetry run python3 bokeh_auth_test.py
python3 -m poetry run python3 uio_test.py
python3 -m poetry run python3 -m pytest  test_json_networking.py
python3 -m poetry run python3 -m pytest -s test_netif.py
python3 -m poetry run python3 -m pytest -s test_ssh.py
python3 -m poetry run python3 -m pytest -s test_conduit.py

echo ""
echo "!!! Check the contents of this file for details of how to run example code"
# The following code provides examples of p3lib use.

# Open browser and display static graphs using plotly.
#python3 -m poetry run ./netplotly_demo.py

# Open browser and show real time plots using bokeh.
# python3 -m poetry run ./time_series_plot_example.py

# Run a more generic bokeh demo showing most of the available widgets
# ./run_bokeh_demo.sh 

# Another bokeh demo using a particular model
# python3 -m poetry run python3 GUIModel_A_example.py

# An example of how to launch another bokeh app in another browser window
# from a bokeh app already running in a browser window.
# python3 -m poetry run python3  bokeh_multiple_app_example.py

# An example of using the tool to generate a bokeh credentials file that can be used 
# to add username/password access to a bokeh server.
# python3 -m poetry run python3 bokeh_credentials_manager_test.py

# A nicegui example
# python3 -m poetry run python3 ngt_examples.py