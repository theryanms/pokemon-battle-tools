import os


#  Function to parse the game log
def parse_game_log(file_path):
    stats = {
        'game_type': '',
        'tier': '',
        'players': {},
        'turns': 0,
        'faints': [],   # (victim, killer)
        'moves': [],    # (attacker, move)
        'status_effects': [],   # (target, status, source)
    }

    # Track last pokemon that damaged each target pokemon
    last_damage_source = {}

    # Track the last active move user
    current_move_user = None

    # To track most recent move and its effects
    current_move = {}
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()

            # Extract game type and tier
            if line.startswith('|gametype|'):
                stats['game_type'] = line.split('|')[2]
            elif line.startswith('|tier|'):
                stats['tier'] = line.split('|')[2]

            # Extract player names
            elif line.startswith('|player|'):
                parts = line.split('|')
                player_num, player_name = parts[2], parts[3]
                stats['players'][player_num] = player_name

            #####################################################################################################

            # Track moves used and store who is doing what
            elif line.startswith('|move|'):
                parts = line.split('|')
                pokemon, move, target = parts[2], parts[3], parts[4]
                current_move = {'pokemon': pokemon, 'move': move, 'target': target}
                stats['moves'].append((pokemon, move))

            elif line.startswith('|-damage|'):
                parts = line.split('|')
                target = parts[2]

                if '[from]' not in line and current_move:
                    last_damage_source[target] = pokemon

                elif '[from]' in line and current_move:
                    for statused_pokemon, status, source in stats['status_effects']:
                        if statused_pokemon == target:
                            last_damage_source[target] = source

            # Track status effects
            elif line.startswith('|-status|'):
                parts = line.split('|')
                target_pokemon, status = parts[2], parts[3]
                source = last_damage_source.get(target_pokemon, pokemon)
                stats['status_effects'].append((target_pokemon, status, source))

            # Track faints and their cause
            elif line.startswith('|faint|'):
                parts = line.split('|')
                fainted_pokemon = parts[2]
                faint_cause = last_damage_source.get(fainted_pokemon, 'unknown')

                # Exclude self-inflicted faints
                if faint_cause and faint_cause != fainted_pokemon:
                    killer_side = faint_cause.split(':')[0][:2]
                    victim_side = fainted_pokemon.split(':')[0][:2]
                    if killer_side == victim_side:
                        continue

                    stats['faints'].append((fainted_pokemon, faint_cause))

            #####################################################################################################

            # Track turns
            elif line.startswith('|turn|'):
                stats['turns'] += 1

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
        f.write(f"Total Turns: {stats['turns']}\n")

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
