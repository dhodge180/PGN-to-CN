"""
This program takes as input a list of PGNs, like from the van der Heiden database
It reads Event, Composer, starting FEN (and who to move), and moves.
It converts to ChessNavigator notation.
Title: [Author -- Tourney]
FEN: [starting FEN]
Subtext: [Black to play:] Win/Draw
Moves: [Mainline only]

It strips out all except the mainline, and converts san into uci using python-chess.

Commandline syntax is:
python PGN_to_CN.py input.pgn [--n-knights] > output.txt

--n-knights is optional, without it knights are converted to S/s in the output.
"""

import re
import chess


def format_name(name_str):
    """
    Format a single author name: Becker=R → Becker, R; underscores → spaces.
    """
    name_str = name_str.replace('_', ' ')
    if '=' in name_str:
        last, initial = name_str.split('=', 1)
        return f"{last}, {initial}"
    return name_str


def format_title(white_str):
    """
    Handle one or more authors in the White field.
    Authors are space-separated tokens each containing '=', e.g.:
      'Becker=R'                      → 'Becker, R'
      'Minski=M Slumstrup_Nielsen=S'  → 'Minski, M & Slumstrup Nielsen, S'
    """
    names = white_str.split()
    authors = [format_name(n) for n in names if '=' in n]
    # If somehow no = found, fall back to the raw string
    if not authors:
        authors = [white_str.replace('_', ' ')]
    return ' & '.join(authors)


def format_subtext(result, fen):
    """Build the Subtext field, prepending 'Black to Play: ' when FEN says b."""
    result_map = {
        '1-0':     'Win',
        '1/2-1/2': 'Draw',
        '0-1':     'Black wins',
    }
    subtext = result_map.get(result, result)

    # FEN active colour is the second space-separated field
    fen_parts = fen.split()
    if len(fen_parts) >= 2 and fen_parts[1] == 'b':
        subtext = f"Black to Play: {subtext}"

    return subtext


def parse_pgn(pgn_text):
    """
    Parse a PGN string containing one or more games.
    Returns a list of dicts with keys: title, fen, subtext.
    Games without a FEN header are skipped.
    """
    # Split into individual games on a blank line followed by a new [Event tag
    game_blocks = re.split(r'\n(?=\[Event )', pgn_text.strip())

    games = []
    for block in game_blocks:
        # Extract all header tags
        headers = {}
        for match in re.finditer(r'\[(\w+)\s+"([^"]*)"\]', block):
            headers[match.group(1)] = match.group(2)
        
        # -------------------------
        # Extract moves starting at the first move line
        # -------------------------
        match_moves = re.search(r'(?m)^(1\.|1\.\.\.).*$', block)
        raw_moves = block[match_moves.start():].strip() if match_moves else ''
        
        # -------------------------
        # Clean moves step by step
        # -------------------------
        clean_moves = raw_moves
        clean_moves = re.sub(r'\{[^}]*\}', '', clean_moves)   # remove comments brackets {…}
        while re.search(r'\([^()]*\)', clean_moves):
            clean_moves = re.sub(r'\([^()]*\)', '', clean_moves) # remove (...) brackets, loop to deal with nested
        clean_moves = re.sub(r'\$\d+', '', clean_moves)     # remove $1 $2 etc..
        clean_moves = re.sub(r'\d+\.(\.\.)?', '', clean_moves)  # remove move numbers
        clean_moves = re.sub(r'\b(1-0|0-1|1/2-1/2)\b', '', clean_moves)  # remove game result
        clean_moves = re.sub(r'\s+', ' ', clean_moves).strip()  # collapse whitespace    

        # Skip games with no FEN
        #if 'FEN' not in headers:
        #    continue

        title   = f"{format_title(headers.get('White', ''))} \u2013 {headers.get('Event', '')}"
        fen     = headers.get('FEN', 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1') # Read from header, else set starting position
        subtext = format_subtext(headers.get('Result', ''), fen)
        moves = clean_moves

        games.append({
            'title':   title,
            'fen':     fen,
            'subtext': subtext,
            'moves': moves,
            
        })

    return games

def convert_line_to_uci(fen, moves):
    """
    Convert a single lines of moves applied from FEN into uci notation
    """
    board = chess.Board(fen)
    uci_list = []
    move_list = moves.split()

    for mv in move_list:
        #print(f"Move {mv}\n")
        # Remove check/mate symbols
        mv = re.sub(r'[+#]', '', mv)
        # Convert SAN to UCI
        try:
            move_obj = board.push_san(mv)
            uci_list.append(move_obj.uci())
        except Exception as e:
            print(f"Warning: couldn't convert move '{mv}' from FEN {fen}")
            uci_list.append(mv)  # fallback to original SAN
    return uci_list


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import sys, pathlib, argparse
    
    parser = argparse.ArgumentParser(description="Convert a PGN into ChessNavigator format")
    parser.add_argument('pgn_filename', help='Path to PGN file')
    parser.add_argument('--n-knights', action='store_true', help="Keep knights as N/n in FEN (no S/s conversion)")
    args = parser.parse_args()
    
    try:
        pgn_text = pathlib.Path(args.pgn_filename).read_text()
    except FileNotFoundError:
        print(f"Error: file '{args.pgn_filename}' not found")
        sys.exit(1)
    
    results = parse_pgn(pgn_text)
    for i, g in enumerate(results, 1):
        fen = g['fen']
        
        moves = g['moves']
        uci_line = convert_line_to_uci(fen, moves)
        uci_line = ' '.join(uci_line)
        
        if not args.n_knights:
            fen = fen.replace("N","S").replace('n','s')
                
        print(f"Game {i}")
        print(f"Title:   {g['title']}")
        print(f"FEN:     {fen}")
        print(f"Subtext: {g['subtext']}")
        #print(f"Moves:   {g['moves']}")
        print(f"Moves:   {uci_line}")
        
        print()
        
    