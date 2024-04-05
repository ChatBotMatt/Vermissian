import os

def get_spreadsheet_id_filepath(guild_id: int):
    spreadsheet_id_path = os.path.join('guilds', str(guild_id), 'spreadsheet_id')

    return spreadsheet_id_path

def add_spreadsheet_id(guild_id: int, spreadsheet_id: str):

    spreadsheet_id_filepath = os.path.join('guilds', str(guild_id), 'spreadsheet_id.txt')

    spreadsheet_id_dirpath = os.path.dirname(spreadsheet_id_filepath)

    os.makedirs(spreadsheet_id_dirpath, exist_ok=True)

    with open(spreadsheet_id_filepath, 'w') as f:
        f.write(spreadsheet_id)

def get_spreadsheet_id_for_guild(guild_id: int) -> str:
    spreadsheet_id_filepath = get_spreadsheet_id_filepath(guild_id)

    if not os.path.exists(spreadsheet_id_filepath):
        raise FileNotFoundError(f'Cannot find spreadsheet ID for guild "{guild_id}".')

    with open(spreadsheet_id_filepath, 'r') as f:
        spreadsheet_id = f.read().strip()

    return spreadsheet_id
