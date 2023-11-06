import glob
import json
import os

language = os.getenv('LANGUAGE') or 'uk'


def load_json_to_dict(language):
    with open(f'/app/locales/{language}.json', mode='r') as infile:
        dictionary = json.load(infile)

    return dictionary


def wrap_as_variable(str):
    return '"' + str + '"'


def wrap_as_tag(str):
    return '>' + str + '<'


def localize(dict):
    file_path = glob.glob('/app/client/dist/app.*.js')[0]
    with open(file_path) as file:
        file_string = file.read()

    for key, value in dict.items():
        if " " in key:
            file_string = file_string.replace(key, value.replace("'", "\\'"))
        file_string = file_string.replace(wrap_as_tag(key), wrap_as_tag(value.replace("'", "\\'")))
        file_string = file_string.replace(wrap_as_variable(key), wrap_as_variable(value.replace("'", "\\'")))

    with open(file_path, 'w') as out:
        out.write(file_string)


if language != 'en':
    translations = load_json_to_dict(language)
    localize(translations)
