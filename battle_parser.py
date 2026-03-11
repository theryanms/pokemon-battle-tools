import os


# Parses the html battle name and removes the slot character, allowing to keep team designation
def get_name_only(battle_name):
    if ':' not in battle_name:
        return battle_name
    team = battle_name.split(':')[0][:2]
    name = battle_name.split(':', 1)[1].strip()

    name = team + ':' + name

    return name


# Parses hp text to extract the current total
def parse_hp_percent(hp_text):
    hp_text = hp_text.strip()

    if hp_text.startswith('0 fnt'):
        return 0.0

    hp_text = hp_text.split(' ')[0]
    if '/' not in hp_text:
        return None

    current, total = hp_text.split('/')
    current = current[:-1]
    current = float(current)
    total = float(total)

    if total != 100:
        factor = total / 100
        total = total / factor
        current = current / factor

        total = round(total, 2)
        current = round(current, 2)

    try:
        if total == 0:
            return None
        return current
    except:
        return None


#  Function to parse the game log
def parse_game_log(file_path):
    stats = {
        'game_type': '',
        'tier': '',
        'players': {},
        'winner': '',
        'game_turns': 0,
        'faints': [],  # (victim, killer)
        'moves': [],  # (attacker, move)
        'status_effects': [],  # (target, status, source)
        'last_hp': {},
        'ko_totals': {},
        'faint_totals': {},
        'total_damage': {},  # (total damage done by a Pokemon)
        'damage_taken': {},  # (total damage TAKEN by a pokemon)
        'field_turns': {},  # (total number of turns on field)
        'terastallized': [],

        'active_slots': {'p1a': None, 'p1b': None, 'p2a': None, 'p2b': None},
    }

    # Track last Pokémon that damaged each target Pokémon
    last_damage_source = {}

    # Names already counted for FIELD turns this turn
    field_seen_this_turn = set()

    # Track the last active move user
    current_move_user = None

    # To track most recent move and its effects
    current_move = {}
    with (open(file_path, 'r')) as file:
        for line in file:
            line = line.strip()

            if line.startswith('|t:|' or '|rule|' or '|j|' or '|-boost|' or '|-unboost|' or '|-immune|'
                               or '|-supereffective|' or '|-resisted|' or '|-activate|' or '-singleturn|'):
                continue

            # Extract game type and tier
            elif line.startswith('|gametype|'):
                stats['game_type'] = line.split('|')[2]

            elif line.startswith('|tier|'):
                stats['tier'] = line.split('|')[2]

            # Extract player names
            elif line.startswith('|player|'):
                parts = line.split('|')
                player_num, player_name = parts[2], parts[3]
                stats['players'][player_num] = player_name

            # Extract current HP (starting total + Regenerator)
            elif line.startswith('|switch|'):
                parts = line.split('|')
                if len(parts) >= 5:
                    battle_name, hp_text = parts[2], parts[4]
                    pokemon = get_name_only(battle_name)
                    hp_percent = parse_hp_percent(hp_text)
                    if hp_percent is not None:
                        stats['last_hp'][pokemon] = hp_percent
                    if pokemon not in field_seen_this_turn:
                        stats['field_turns'][pokemon] = stats['field_turns'].get(pokemon, 0) + 1
                        field_seen_this_turn.add(pokemon)

            # Track moves used and store who is doing what
            elif line.startswith('|move|'):
                parts = line.split('|')
                pokemon = get_name_only(parts[2])
                move = parts[3]
                target = get_name_only(parts[4])
                current_move = {'pokemon': pokemon, 'move': move, 'target': target}
                stats['moves'].append((pokemon, move))

            elif line.startswith('|-heal|'):
                parts = line.split('|')
                pokemon = get_name_only(parts[2])
                hp_text = parts[3]

                # Parsing for new hp total
                new_hp = parse_hp_percent(hp_text)

                ####### DO SOME HEALING CALCS HERE?!?!?!? #####
                # old_hp = stats['last_hp'].get(pokemon)
                # delta to new hp
                # add to total healing received / given

                if new_hp is not None:
                    stats['last_hp'][pokemon] = new_hp

            elif line.startswith('|-damage|'):
                parts = line.split('|')
                target = get_name_only(parts[2])
                hp_text = parts[3]

                # Parsing for new hp total
                new_hp = parse_hp_percent(hp_text)

                # Retrieving previous hp total
                old_hp = stats['last_hp'].get(target)

                # Updating last_hp if valid value
                if new_hp is not None:
                    stats['last_hp'][target] = new_hp

                damage_delta = old_hp - new_hp
                if damage_delta <= 0:
                    continue

                # Damage taken from a valid attack move
                if '[from]' not in line:
                    stats['total_damage'][pokemon] = stats['total_damage'].get(pokemon, 0) + damage_delta

                    stats['damage_taken'][target] = stats['damage_taken'].get(target, 0) + damage_delta

                    last_damage_source[target] = pokemon

                # Damage taken from a status effect
                elif '[from]' in line:
                    for statused_pokemon, status, source in stats['status_effects']:
                        if statused_pokemon == target:
                            stats['total_damage'][source] = stats['total_damage'].get(source, 0) + damage_delta

                            stats['damage_taken'][target] = stats['damage_taken'].get(target, 0) + damage_delta

                            last_damage_source[target] = source

            # Track status effects
            elif line.startswith('|-status|'):
                parts = line.split('|')
                target_pokemon = get_name_only(parts[2])
                status = parts[3]
                source = last_damage_source.get(target_pokemon, pokemon)
                stats['status_effects'].append((target_pokemon, status, source))

            # Track faints and their cause
            elif line.startswith('|faint|'):
                parts = line.split('|')
                fainted_pokemon = get_name_only(parts[2])
                faint_cause = last_damage_source.get(fainted_pokemon, 'unknown')

                # Exclude self and team-inflicted faints
                if faint_cause and faint_cause != fainted_pokemon:
                    killer_side = faint_cause.split(':')[0][:2]
                    victim_side = fainted_pokemon.split(':')[0][:2]
                    if killer_side == victim_side:
                        continue

                    stats['faints'].append((fainted_pokemon, faint_cause))
                    stats['ko_totals'][faint_cause] = stats['ko_totals'].get(faint_cause, 0) + 1
                    stats['faint_totals'][fainted_pokemon] = stats['faint_totals'].get(fainted_pokemon, 0) + 1

            elif line.startswith('|-terastallize|'):
                parts = line.split('|')
                tera_pokemon = parts[2]
                tera_pokemon = get_name_only(tera_pokemon)
                tera_type = parts[3]
                stats['terastallized'].append((tera_pokemon, tera_type))

            elif line.startswith('|win|'):
                parts = line.split('|')
                stats['winner'] = parts[2]

            # Track turns
            elif line.startswith('|turn|'):
                stats['game_turns'] += 1

                # THIS SHIt IS FUCKED AND NEEDS TO BE REDONE
                # new turn, reset who we have seen
                field_seen_this_turn = set()
                #
                for name in field_seen_this_turn:
                    print(name)

                    if name not in field_seen_this_turn:
                        stats['field_turns'][name] = stats['field_turns'].get(name, 0) + 1
                        field_seen_this_turn.add(name)

    return stats


def save_results(stats, output_folder, file_name):
    # Create the file path
    output_path = os.path.join(output_folder, file_name)

    with open(output_path, 'w') as f:

        # Write metadata
        f.write(f"Game Type: {stats['game_type']}\n")
        f.write(f"Tier: {stats['tier']}\n")
        f.write(f"Players:\n")
        for player_num, player_name in stats['players'].items():
            f.write(f"  {player_num}: {player_name}\n")

        f.write(f"\nWinner: {stats['winner']}\n")

        f.write(f"\nTotal Turns: {stats['game_turns']}\n")

        ### Pokemon Brought using LAST HP in stats. Will be a value if they appeared in match
        f.write(f"\nPokemon Brought:\n")
        for pokemon in sorted(stats['last_hp'].items(), key=lambda x: (x[0].lower())):
            f.write(f"  {pokemon}\n")

        f.write(f"\nPokemon Terastallized:\n")
        for pokemon, tera_type in stats['terastallized']:
            f.write(f"  {pokemon}: {tera_type}\n")

        f.write(f"\nTurns on Field\n")
        for pokemon, turns in sorted(stats['field_turns'].items(), key=lambda x: (-x[1], x[0].lower())):
            f.write(f"    {pokemon}: {turns}\n")

        f.write(f"\nKO Totals\n")
        for pokemon, kos in sorted(stats['ko_totals'].items(), key=lambda x: (-x[1], x[0].lower())):
            f.write(f"    {pokemon}: {kos}\n")

        f.write(f"\nFaint Totals\n")
        for pokemon, faints in sorted(stats['faint_totals'].items(), key=lambda x: (-x[1], x[0].lower())):
            f.write(f"    {pokemon}: {faints}\n")

        f.write(f"\nDamage Dealt (approx %)\n")
        for pokemon, damage in sorted(stats['total_damage'].items(), key=lambda x: (-x[1], x[0].lower())):
            f.write(f"    {pokemon}: {int(damage)}\n")

        f.write(f"\nDamage Taken (approx %)\n")
        for pokemon, damage in sorted(stats['damage_taken'].items(), key=lambda x: (-x[1], x[0].lower())):
            f.write(f"    {pokemon}: {int(damage)}\n")

        ### DAMAGE HEALED?!?!?!

        # Write faints with the attacker who caused it
        f.write("\nFaints\n")
        for fainted_pokemon, attacker in stats['faints']:
            f.write(f"  {fainted_pokemon} was fainted by {attacker}\n")

        f.close()

    print(f"Results printed to {output_path}")


# Function to process all .html files in the folder
def process_all_logs(input_folder, output_folder):
    for file_name in os.listdir(input_folder):
        if file_name.endswith(".html"):
            file_path = os.path.join(input_folder, file_name)
            print(f"Processing {file_name}...")

            game_stats = set()

            # Parse the game log
            game_stats = parse_game_log(file_path)

            # Create a unique results file name based on the input file name
            result_file_name = f"Results_{file_name.replace('.html', '')}.txt"

            ######
            # SPLIT THE FILE NAME TO MAKE IT SHORTER / JUST USERS NAMES ++
            ######

            # Save the results
            save_results(game_stats, output_folder, result_file_name)


########## CHANGE BELOW TO YOUR OWN INPUT/OUTPUT FOLDERS
input_folder = "C:/Users/ryanm/OneDrive/Desktop/PokeStats"
output_folder = "D:/Documents/GitHub/dev/pokemon-battle-tools/results"
process_all_logs(input_folder, output_folder)
