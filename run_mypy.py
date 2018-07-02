import subprocess
import sys
modules = ["gamesimulator/action.py",
           "gamesimulator/game.py",
           "gamesimulator/plot.py",
           "gamesimulator/random_.py",
           "gamesimulator/tournament.py",
           "gamesimulator/strategies/cooperator.py",
           "gamesimulator/strategies/defector.py",
           "gamesimulator/strategies/template.py"]

exit_codes = []
for module in modules:
    rc = subprocess.call(["mypy", "--ignore-missing-imports",
                          "--follow-imports", "skip", module])
    exit_codes.append(rc)
sys.exit(max(exit_codes))
