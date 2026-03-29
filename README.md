This program takes as input a .pgn file (which can be a list of games/studies), like from the van der Heiden database.

It reads Event, Composer (from the White field), starting FEN (and who to move), and moves.  
It converts to ChessNavigator notation.  
Title: [Author -- Tourney]  
FEN: [starting FEN]  
Subtext: [Black to play:] Win/Draw  
Moves: [Mainline only]  

It strips out all except the mainline, and converts san into uci using python-chess.

Commandline syntax is:  
python PGN_to_CN.py input.pgn [--n-knights] > output.txt  

--n-knights is optional, without it knights are converted to S/s in the output.

