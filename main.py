import csv
import glob


def load_excel_to_dict():
    d = {}
    with open('redash_localization_words.csv', mode='r') as infile:
        reader = csv.reader(infile)
        for rows in reader:
            d[rows[0]] = rows[1]

    return d


def wrap_as_variable(str):
    return '"' + str + '"'


def wrap_as_tag(str):
    return '>' + str + '<'


def localize(dict):
    file_path = glob.glob('app.*.js')[0]
    with open(file_path) as file:
        file_string = file.read()
        
    for key, value in dict.items():
        if " " in key:
            file_string = file_string.replace(key, value.replace("'",  "\\'"))
        file_string = file_string.replace(wrap_as_tag(key), wrap_as_tag(value.replace("'", "\\'")))
        file_string = file_string.replace(wrap_as_variable(key), wrap_as_variable(value.replace("'", "\\'")))

    with open(file_path, 'w') as out:
        out.write(file_string)


translations = load_excel_to_dict()
localize(translations)


# Redefine default access rights permissions

def refactor_permissions(refactor_list, change_from, change_to):
    for script in refactor_list:
        file_path = glob.glob(script)[0]
        with open(file_path, 'r') as file:
            initial = file.read()
            if change_from not in initial:
                change_from = change_from.replace('"', "'")
                change_to = change_to.replace('"', "'")
            refactored = initial.replace(change_from, change_to)
        with open(file_path, 'w') as file:
            file.write(refactored)


ADMIN_SCRIPT_LIST = [
    'redash/cli/users.py',
    'redash/handlers/setup.py',
    'redash/models/__init__.py',
               ]
DEFAULT_SCRIPT_LIST = ['redash/models/users.py']
ADMIN_PERMISSIONS_CURRENT = '"admin", "super_admin"'
EDITOR_PERMISSIONS = '"create_dashboard", "create_query", "edit_dashboard", "edit_query"'
LIST_USERS = '"list_users"'
ADMIN_PERMISSIONS_REFACTORED = f'{ADMIN_PERMISSIONS_CURRENT}, {EDITOR_PERMISSIONS}, {LIST_USERS}'
INDENT = '        '
NL = '\n'


refactor_permissions(ADMIN_SCRIPT_LIST, f'[{ADMIN_PERMISSIONS_CURRENT}]', f'[{ADMIN_PERMISSIONS_REFACTORED}]')
refactor_permissions(DEFAULT_SCRIPT_LIST, f'{INDENT}{EDITOR_PERMISSIONS.replace(", ", f",{NL}{INDENT}")},{NL}', '')
refactor_permissions(DEFAULT_SCRIPT_LIST, f'{INDENT}{LIST_USERS},{NL}', '')