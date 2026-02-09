Halite III Match Manager
-----------------------
This is a Python package which can run many games between local bots, producing ranking data which is stored in an sqlite3 database.

This was adapted from the Halite II match manager. Some bugs and legacy code may remain.


Forked from
https://gitlab.com/smiley1983/halite3-match-manager


Usage
-----

Command line script "halite3-match-manager/manager.py" provides an easy access interface.

Run the commandline like:
```
    ./manager.py (when in halite3-match-manager directory)
    python3 . (when in halite3-match-manager directory)
    python3 -m h3m (if package is installed)
```


Examples of Bash command line invocation are shown below.

To add a bot:
```
    ./manager.py -A botname ./path/to/bot  # C or other executable
    ./manager.py -A botname "python3 ./path/to/MyBot.py"  # python bot
```

To activate/deactivate/delete/play/reset a bot:
```
    ./manager.py -a botname      # activate bot
    ./manager.py -d botname      # deactivate bot
    ./manager.py -D botname      # delete bot
    ./manager.py -b botname      # force bot to play
    ./manager.py -rb botname     # reset bot stats
    ./manager.py --activateAll   # activate all bots in database
    ./manager.py --deactivateAll # deactivate all bots in database
```

To run matches:
```
    ./manager.py -m      # run single match
    ./manager.py -mm N   # run N matches (keypress of <Q> or <ESC> will cause interrupt after current match)
    ./manager.py -f      # run forever (keypress of <Q> or <ESC> will cause interrupt after current match)
```

To show results:
```
    ./manager.py -r         # display bot rank table
    
    ./manager.py -R 0       # show last 10 games
    ./manager.py -R 0 -L 5  # show last 5 games
    ./manager.py -R 10 -L 5 # show 5 games, starting at 10 games ago
```

To visualize match:
```
    ./manager.py -V 16037  # play match_id 16037 (see id's with -R)
    ./manager.py -V 0      # play last
    ./manager.py -V -1     # play second to last, etc.
    ./manager.py -m -V 0   # run match and visualize after

    # View a replay file by name
    ./manager.py -F /path/to/replay.hlt
```

Advanced match options:
```
    ./manager.py -t NNN  # set turn limit
    ./manager.py -nr     # set no-replays
    ./manager.py -nl     # set no-logs
    ./manager.py -nt     # set no-timeout

    -p {N,N,N}   # player count distribution eg. {2,4}
    -p N         # player count is N
    
    -M {N,N,N}   # map size distribution eg. {32,40,48,56,64}
    -M N         # map size is N
```

Advanced database and logging options:
```
    --config  # Show configuration settings in database
    --clear   # Clear *.log and replay files (in ./ and in replay directory set in manager.py)
    --reset   # Builds fresh database keeping bots and settings
```


Installation
-----

See recommended setup and configuration [unix script](recommended_setup.sh)

#### Manager Package
    git clone https://gitlab.com/timjolson/halite3-match-manager
    pip3 install -e halite3-match-manager

### Configure Manager options (saved in database file):
    # halite executable
    ./manager.py --halite '../path/to/halite.exe'
    
    # replay directory
    ./manager.py --replay_dir '../path/to/replays'
    
    # visualizer command
    # FILENAME gets replaced at runtime for each usage
    ./manager.py --visalizer "vis.exe -opt1 FILENAME opt2"

#### Fluorine Visualizer example
    ## Install npm : https://www.npmjs.com/get-npm
    apt install npm

    ## Install electron to run locally or gobally
    ## This may take a while
    npm install electron     # Local
    npm install -g electron  # Global

    ## Install fluorine
    git clone https://github.com/fohristiwhirl/fluorine
    cd fluorine
    npm install
    cd ..
    
    ## Run fluorine on a replay file
    # Local electron install
    ./node_modules/.bin/electron ./fluorine -o replay_file.hlt
    
    # Global electron install
    electron ./fluorine -o replay_file.hlt
