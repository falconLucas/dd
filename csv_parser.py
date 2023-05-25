import json
import csv
import yaml

def build_descriptor_dict(data_out: dict, path: list, format, name, type, context):
    key = path[0]
    if isinstance(data_out, str):
        return data_out
    if key not in data_out:
        if len(path) == 1:
            data_out[key] = {
                "data": format,
                "metadata": {"Name": name, "Context": context, "Type": type},
            }
        else:
            data_out[key] = {}
            data_out[key] = {
                "data": build_descriptor_dict(
                    data_out[key], path[1:], format, name, type, context
                ),
                "metadata": {"Name": name, "Context": context, "Type": type},
            }
    else:
        if len(path) == 1:
            data_out[key] = {
                "data": format,
                "metadata": {"Name": name, "Context": context, "Type": type},
            }
        elif isinstance(data_out[key], dict):
            build_descriptor_dict(data_out[key]['data'], path[1:], format, name, type, context)
        else:
            data_out[key] = {
                "data": format,
                "metadata": {"Name": name, "Context": context, "Type": type},
            }
    return data_out


def derive_lists(data_in: dict):
    data_out = data_in
    if isinstance(data_in, dict):
        if "[" in list(data_in.keys())[0]:
            data_out = []
            for key, value in data_in.items():
                data_out.append(derive_lists(value))
        else:
            data_out = {}
            for key, value in data_in.items():
                data_out[key] = derive_lists(value)
    return data_out


def get_value_from_path(data_dict: dict, path: list):
    # get the object inside data_dict pointed to by the path (list of keys in depth order)
    key = path[0]
    return_val = None
    if len(path) == 1:
        if isinstance(data_dict, dict) and key in data_dict:
            return_val = data_dict[key]
    else:
        return_val = get_value_from_path(data_dict[path[0]]["data"], path[1:])
    return return_val

def generate_template_dict(descriptor:dict) -> dict:
    data_template_dict = {}
    for key, value in descriptor.items():
        if isinstance(value, dict):
            if isinstance(value['data'], dict):
                data_template_dict[key] = generate_template_dict(value['data'])
            elif isinstance(value['data'], list):
                data_template_dict[key] = [generate_template_dict(item) for item in value['data']]
            else:
                data_template_dict[key] = value['data']
        else:
            data_template_dict[key] = value
    return data_template_dict

def generate_descriptor_dict(csv_data: list) -> dict:
    descriptor_dict = {}
    for row in csv_data[1:]:
        name = row[0]
        path = row[4].split("->")
        type = row[5]
        format = row[2]
        context = row[6]
        if type != "List" and type != "Dict":
            build_descriptor_dict(descriptor_dict, path, format, name, type, context)
    for row in csv_data:
        name = row[0]
        path = row[4].split("->")
        type = row[5]
        context = row[6]
        item = get_value_from_path(descriptor_dict, path)
        if isinstance(item, dict):
            item["metadata"] = {"Name": name, "Context": context, "Type": type}
    return descriptor_dict

class CSVParser:
    def __init__(self):
        self.datagram_descriptor = None
        self.template = None
        self.csv_data = None
    def parse(self, csv_file_name: str):
        with open(csv_file_name, "r") as csv_file:
            csv_reader = csv.reader(csv_file)
            self.csv_data = list(csv_reader)
    def generate_descriptor(self):
        self.datagram_descriptor = generate_descriptor_dict(self.csv_data)
    def generate_template(self):
        self.template = derive_lists(generate_template_dict(self.datagram_descriptor))
    def dump_json(self, json_file_name: str, mode: str = "w", template: bool = False):
        if template:
            json_data = self.template
        else:
            json_data = self.datagram_descriptor
        with open(json_file_name, mode) as json_file:
            json.dump(json_data, json_file, indent=4, sort_keys=True)
    def dump_yaml(self, yaml_file_name: str, mode: str = "w", template: bool = False):
        if template:
            yaml_data = self.template
        else:
            yaml_data = derive_lists(self.datagram_descriptor)
        with open(yaml_file_name, mode) as yaml_file:
            yaml.dump(yaml_data, yaml_file, indent=4)

def test():
    test_data = {
        "[0]": 0,
        "[1]": 1,
        "[2]": 2,
        "[3]": 3,
        "[4]": 4,
        "[5]": {
            "[0]": 0,
            "[1]": 1,
            "[2]": 2,
            "[3]": 3,
            "[4]": 4,
            "[5]": {"[0]": 0, "[1]": 1, "[2]": 2, "[3]": 3, "[4]": 4},
        },
    }
    print(test_data)
    print(derive_lists(test_data))
    test_data = {
        "a": {"a": {"a": 1, "b": 2}, "b": {"a": 3, "b": 4}},
        "b": {"a": {"a": 5, "b": 6}, "b": {"a": 7, "b": 8}},
    }
    item = get_value_from_path(test_data, ["b", "a", "a"])
    item = 0
    print(test_data)


if __name__ == "__main__":
    p = CSVParser()

    p.parse("input/datagram-descriptor.csv")
    p.generate_descriptor()
    p.dump_json("output/datagram-descriptor.json")
    p.dump_yaml("output/datagram-descriptor.yaml")
    p.generate_template()
    p.dump_json("output/template.json", template=True)
    p.dump_yaml("output/template.yaml", template=True)