#!/bin/bash
# Set up the needed dependencies on Ubuntu 16.04/18.04

# Mapbox SDK (for Python)
sudo apt install python3-pip
#pip3 install boto3 iso3166 python-dateutil requests polyline uritemplate cachecontrol
#mkdir ~/development/
#cd ~/development/
#git clone https://github.com/mapbox/mapbox-sdk-py.git
pip3 install mapbox requests geopy




export PYTHONPATH=~/development/mapbox-sdk-py/:~/development/multi-prop-router/src/

# This is the "public" token to access the Mapbox API
export MAPBOX_ACCESS_TOKEN=$(cat mapbox.key)
