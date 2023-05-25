from yaml import load, dump, FullLoader

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from csv_parser import CSVParser


class DatagramDescriptor(CSVParser):
    rules = {}
    items = {}
    descriptor_filename = ""

    def __init__(
        self,
        descriptor_filename: str,
        rules_filename="dd-rules.yaml",
        branch_root: str = "",
    ) -> None:
        super().__init__()
        self.branch_root = branch_root
        self.load_rules(rules_filename)
        self.load_items(descriptor_filename)
        self.descriptor_filename = descriptor_filename

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
        self.generate_descriptor()
        self.items = self.datagram_descriptor

    def load_items(self, filename: str) -> None:
        if "yaml" in filename:
            self._load_items_yaml(filename)
        elif "csv" in filename:
            self._load_items_csv(filename)
        if self.branch_root != "" and self.branch_root in self.items:
            self.items = {self.branch_root: self.items.pop(self.branch_root)}

    def _validate_dict(self, items) -> bool:
        retval = True
        for key, value in items.items():
            for item_field in value["metadata"]:
                if item_field not in self.rules["MetadataWhitelist"]:
                    print("Field " + item_field + " is not in metadata whitelist")
                    return False
            try:
                m = value["metadata"]
                d = value["data"]
                for field, field_rule in self.rules["Fields"].items():
                    if field_rule["IsMeta"] and field_rule["Required"]:
                        if field not in m:
                            print(
                                "Field "
                                + field
                                + " is required but not present in metadata"
                            )
                        elif not isinstance(m[field], field_rule["Type"]):
                            print(
                                "Field " + field + " has invalid type " + type(m[field])
                            )
                            retval = False
                        elif field_rule["Type"] == "str" and len(m[field]) == 0:
                            print(f"Field {field} is empty")
                            retval = False
                    if self._validate_dict(d) == False:
                        return False

            except KeyError as e:
                print(e.with_traceback())
                retval = False
        return retval

    def _validate_csv_list(self, items) -> bool:
        column_names = items[0]
        name_indexes = {}
        for column_name in column_names:
            if column_name not in self.rules["MetadataWhitelist"]:
                print("Field " + column_name + " is not in metadata whitelist")
                return False
            name_indexes[column_name] = column_names.index(column_name)
        for field, field_rule in self.rules["Fields"].items():
            if field_rule["Required"]:
                if field not in column_names:
                    print("Field " + field + " is required but not present")
                    return False
        for item in items[1:]:
            for field, field_rule in self.rules["Fields"].items():
                if field_rule["Required"]:
                    if len(item[name_indexes[field]]) == 0:
                        print(f"Field {field} in {item} is empty")
                        return False
        return True

    def validate(self) -> bool:
        if self.rules == {}:
            print("Rules not loaded")
            return False
        if self.items == {}:
            print("Items not loaded")
            return False
        if "csv" in self.descriptor_filename and len(self.csv_data) != 0:
            return self._validate_csv_list(self.csv_data)
        return self._validate_dict(self.items)


def main():
    # dd = DatagramDescriptor("datagram-descriptor.yaml")
    dd = DatagramDescriptor("input/datagram-descriptor.csv")
    if dd.validate():
        print("Success!")
    else:
        print("Fail!")


if __name__ == "__main__":
    main()
