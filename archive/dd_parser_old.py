from yaml import load, dump, FullLoader

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from csv_parser import CSVParser

class DatagramDescriptor(CSVParser):
    rules = {}
    items = {}

    def __init__(
        self, descriptor_filename: str, rules_filename="dd-rules.yaml"
    ) -> None:
        self.load_rules(rules_filename)
        self.load_items(descriptor_filename)

    def load_rules(self, filename: str) -> None:
        with open(filename, "r") as file:
            self.rules = load(file, Loader=FullLoader)
            file.close()

    def _load_items_yaml(self, filename: str) -> None:
        with open(filename, "r") as file:
            self.items = load(file, Loader=FullLoader)
            file.close()

    def _load_items_csv(self, filename: str) -> None:
        self.parse(filename)
        self.items = self.datagram_descriptor
    def load_items(self, filename: str) -> None:
        if "yaml" in filename:
            self._load_items_yaml(filename)
        elif "csv" in filename:
            self._load_items_csv(filename)

    def _validate(self, items) -> bool:
        retval = True
        for item in items:
            for item_field in item:
                if item_field not in self.rules["FieldWhitelist"]:
                    print("Field " + item_field + " is not in whitelist")
                    return False
            try:
                t = item["Type"]
                if t in self.rules["Types"]:
                    for field in self.rules["Types"][t]["Fields"]:
                        field_name = field["Field"]
                        if field["Required"]:
                            if field["Field"] not in item:
                                print(
                                    "Item "
                                    + item["Name"]
                                    + " is missing field "
                                    + field_name
                                )
                                retval = False
                            elif "Type" in field:
                                type_valid = False
                                for t2 in field["Type"]:
                                    if t2 in str(type(item[field_name])):
                                        type_valid = True
                                        break
                                if not type_valid:
                                    print(
                                        "Field "
                                        + field_name
                                        + " in item "
                                        + item["Name"]
                                        + " is of type "
                                        + str(type(item[field_name]))
                                        + " should be of type "
                                        + str(field["Type"])
                                    )
                                    retval = False
                if retval == True and t == "data":
                    retval = self._validate(item["Data"].copy())

            except KeyError as e:
                print(e.with_traceback())
                retval = False
        return retval

    def validate(self) -> bool:
        return self._validate(self.items)


def main():
    # dd = DatagramDescriptor("datagram-descriptor.yaml")
    dd = DatagramDescriptor("datagram-descriptor.csv")
    if dd.validate():
        print("Success!")
    else:
        print("Fail!")


if __name__ == "__main__":
    main()
