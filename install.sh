#!/bin/sh
# Set up the needed dependencies on Ubuntu 16.04/18.04

# Mapbox SDK (for Python)
sudo apt install python3-pip
pip3 install boto3 iso3166 python-dateutil requests polyline uritemplate
mkdir ~/development/
cd ~/development/
git clone https://github.com/mapbox/mapbox-sdk-py.git





export PYTHONPATH=~/development/mapbox-sdk-py/

# This is the "public" token to access the Mapbox API
export MAPBOX_ACCESS_TOKEN=pk.eyJ1IjoicGllbGVyaWMiLCJhIjoiY2pvZWlmMWRrMWlvNTN3bXJtcHIxaHhjOCJ9.ayBD0fgZo_eylX3GNA_lFg
