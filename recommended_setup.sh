#!/usr/bin/env bash

# This is the recommended setup on a unix system

# Install manager
pip3 install -e .

# Install nodejs
curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash -  # ubuntu 18
apt install nodejs
# Install npm : https://www.npmjs.com/get-npm
apt install npm

# Get fluorine
git clone https://github.com/fohristiwhirl/fluorine
cd fluorine

# Install electron to run locally
# Poor internet service can cause the download to fail
npm install --verbose electron

# Install fluorine
npm install --verbose
cd ..

# Config manager
mkdir replays
./manager.py --halite './halite/manager/halite' --visualizer "./fluorine/node_modules/.bin/electron ./fluorine -o FILENAME" --replay_dir './replays'
