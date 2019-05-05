#!/usr/bin/env bash

# This is the recommended setup on a unix system

# Install manager
pip3 install -e .

# Install npm : https://www.npmjs.com/get-npm
apt install nodejs
apt install npm

# Install electron to run locally
# Poor internet service can cause the download to fail
npm install --verbose electron

# Install fluorine
git clone https://github.com/fohristiwhirl/fluorine
cd fluorine
npm install --verbose
cd ..

mkdir replays
./manager.py --halite './halite/manager/halite' --visualizer "['./node_modules/dist/electron', './fluorine', '-o', 'FILENAME']" --replay_dir './replays'
