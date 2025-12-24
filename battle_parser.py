import os

#  Function to parse the game log
def parse_game_log(file_path)
    stats = {
        'game_type': '',
        'tier': '',
        'players': {},
        'turns': 0,
        'faints': [],
        'moves': [],
        'status_effects': [],
    }

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

    return stats
def save_results(stats, output_folder, file_name):


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

########## CHANGE BELOW TO INPUT FOLDER
input_folder = '.'
process_all_logs(input_folder)