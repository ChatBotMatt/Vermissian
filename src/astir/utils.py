import os
import json
from typing import Dict

from src.astir.AstirMove import AstirMove

def load_moves() -> Dict[str, Dict[str, AstirMove]]:
    if not hasattr(load_moves, 'all_moves'):
        all_moves = {}

        for move_filename in os.listdir(os.path.join('data', 'armour_astir_advent', 'moves')):
            playbook = os.path.splitext(move_filename)[0]

            with open(os.path.join('data', 'armour_astir_advent', 'moves', move_filename), 'r', encoding='utf-8') as f:
                playbook_moves: Dict[str, AstirMove] = {
                    move_name.lower(): AstirMove.from_json(move_name, {** move_data, "playbook": playbook}) for move_name, move_data in
                    json.load(f).items()
                }

            all_moves[playbook] = playbook_moves

        load_moves.all_moves = all_moves

    return load_moves.all_moves
