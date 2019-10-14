import sys
import manager
cmd = manager.Commandline()
cmd.parse(sys.argv[1:])
cmd.act()
