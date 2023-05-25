import json
import csv

def generate_name(key, value) -> str:
    name = key.replace('_', ' ').replace('-', ' ').replace('INT', '').strip('<').strip('>').lower()
    if len(name) == 1 or '[' in name:
        try:
            name = value.replace('_', ' ').replace('-', ' ').replace('INT', '').strip('<').strip('>').lower()
        except AttributeError:
            try:
                name = str(value[0]).replace('_', ' ').replace('-', ' ').replace('INT', '').strip('<').strip('>').lower()
            except:
                pass
    return name

def generate_single_entry(value, parent, key, path) -> list:
    name = generate_name(key, value)
    type = ''
    if isinstance(value, str):
        if 'int' in value.lower():
            type = 'Integer'
        elif 'float' in value.lower():
            type = 'Float'
        else:
            type = 'String'
    elif isinstance(value, int):
        type = 'Integer'
    elif isinstance(value, float):
        type = 'Float'
    return [name, key, value, parent, path, type]

def generate_list(json_data, parent='', path='') -> list:
    data_list = []
    path_to_here = path
    if path != '':
        path_to_here += '->'
    if isinstance(json_data, list):
        index = 0
        for item in json_data:
            if isinstance(item, str):
                data_list.append(generate_single_entry(item, parent, f'[{index}]', path_to_here+f'[{json_data.index(item)}]'))
            else:
                data_list.extend(generate_list(item, parent, path_to_here+f'[{index}]'))
            index += 1
    elif isinstance(json_data, dict):
        for key, value in json_data.items():
            name = generate_name(key, value)
            if isinstance(value, dict):
                data_list.extend(generate_list(value, key, path_to_here+key))
                data_list.append([name, key, '', parent, path_to_here+key, 'Dict'])
            elif isinstance(value, list):
                data_list.extend(generate_list(value, key, path_to_here+key))
                data_list.append([name, key, 'List', parent, path_to_here+key, 'List'])
            else:
                data_list.append(generate_single_entry(value, parent, key, path_to_here+key))
    return data_list

def json_to_csv(json_file_name:str, csv_file_name:str, mode:str='w', context:str=''):
    json_data = None
    data_list = []
    with open(json_file_name, 'r') as json_file:
        json_data = json.load(json_file)

    if mode == 'w':
        data_list.append(["Name", "Key", "Format", "Parent", "Path", "Type", "Context"])
    data_list.extend(generate_list(json_data))
    for row in data_list[1:]:
        row.append(context)
    with open(csv_file_name, mode) as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerows(data_list)
        print(f"Converted {json_file_name} to {csv_file_name}")


if __name__ == "__main__":
    json_to_csv("V1_config.json", "data.csv", context='Config')
    json_to_csv("V1.json", "data.csv", mode='a', context='Config')
    json_to_csv("V2.json", "data.csv", mode='a', context='State')
    json_to_csv("V3_stats.json", "data.csv", mode='a', context='Stats')
    json_to_csv("V3_data.json", "data.csv", mode='a', context='Data')