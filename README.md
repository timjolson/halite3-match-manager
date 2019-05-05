Halite III Match Manager
-----------------------
This is a Python package which can run many games between local bots, producing ranking data which is stored in an sqlite3 database.

This was adapted from the Halite II match manager. Some bugs and legacy code may remain.


Usage
-----

Command line script "halite3-match-manager/manager.py" provides an easy access interface.

Examples of Bash command line invocation are shown below.

To add a bot:
```
    ./manager.py -A botname ./path/to/bot  # C or other executable
    ./manager.py -A botname "python3 ./path/to/MyBot.py"  # python bot
```

To activate/deactivate/delete/play/reset a bot:
```
    ./manager.py -a botname
    ./manager.py -d botname
    ./manager.py -D botname
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
    ./manager.py -R 10      # show 10 games up to 10th to last played
    ./manager.py -R 10 -L 5 # show 5 games up to 10th to last played
```

To visualize match:
```
    ./manager.py -V 16037  # play match_id 16037 (see id's with -R)
    ./manager.py -V 0      # play last
    ./manager.py -V -1     # play second to last, etc.
    ./manager.py -m -V 0   # run match and visualize after
```

To visualize a replay file:
```
    ./manager.py -F /path/to/replay.hlt
```

Increase verbosity (manager is nearly silent otherwise):
```
    ./manager.py -v ...
    ./manager.py -vv ...
    ./manager.py -vvv ...
```

Advanced options:
```
    ./manager.py -W NNN  # set map width
    ./manager.py -H NNN  # set map height
    ./manager.py -s NNN  # set map seed
    ./manager.py -t NNN  # set turn limit
    ./manager.py -n      # set no-replays
    ./manager.py -l      # set no-logs
    ./manager.py -nt     # set no-timeout

    -p {N,N,N}  OR  --players {N,N,N}   # player count distribution eg. {2,4}
    -p N        OR  --players N         # player count is N
    
    --maps {N,N,N}        # map size distribution eg. {32,40,48,56,64}
    --maps N              # map size is N
```

Clear *.log and replay files (in ./ and in replay directory set in manager.py):
```
    --clear  # clearing happens before other commands are run
    --reset  # builds new database (no records), keeping bots and options
```


Installation
-----

See recommended setup and configuration [unix script](https://gitlab.com/timjolson/halite3-match-manager/blob/master/recommended_setup.sh)

#### Manager Package
    git clone https://gitlab.com/timjolson/halite3-match-manager
    pip install -e halite3-match-manager

#### Visualizer (fluorine example)
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
    
    ## Run fluorine on a replay file
    # Local electron install
    ./node_modules/.bin/electron . -o replay_file.hlt
    
    # Global electron install
    electron . -o replay_file.hlt

### Configure Manager options (saved in database file):

    # halite executable
    ./manager.py --halite '../path/to/halite.exe'
    
    # replay directory
    ./manager.py --replay_dir '../path/to/replays'
    
    # visualizer command
    # FILENAME gets replaced at runtime for each usage
    # this example runs command "vis.exe opt1 FILENAME opt2"
    ./manager.py --visalizer "['vis.exe', 'opt1', 'FILENAME', 'opt2']"
