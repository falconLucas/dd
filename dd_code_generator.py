from dd_parser import DatagramDescriptor

import json
import os
import sys
import optparse
import random
import string


def error(text):
    sys.stderr.write("Error: %s\n" % text)
    sys.exit(-1)


class CodeGenerator(DatagramDescriptor):
    def __init__(
        self,
        descriptor_filename: str,
        rules_filename="dd-rules.yaml",
        data_allocation="dynamic",
        branch_root="",
    ) -> None:
        super().__init__(descriptor_filename, rules_filename, branch_root=branch_root)
        self.datagram_is_valid = self.validate()
        self.read_templates()
        self.symbol_table = {}

    def read_templates(self):
        self.templates = {}
        for template_key, template_file in self.rules["Templates"].items():
            with open(self.rules["Templates"][template_key]) as file:
                self.templates[template_key] = file.read()

    def build_symbol_name(self, item: dict, suffix="") -> str:
        symbol = item["metadata"]["Name"].replace(" ", "_") + suffix
        if symbol in self.symbol_table:
            self.symbol_table[symbol] += 1
        else:
            self.symbol_table[symbol] = 1
        return symbol

    def template_build_random_value(self, item: dict):
        type = item["Type"]
        if type == "character":
            return random.choice(string.ascii_letters)
        elif type == "string":
            return "Hello world!"
        elif type == "integer":
            return random.randrange(
                item["ValueMin"], item["ValueMax"], item["Resolution"]
            )
        elif type == "floating_point":
            return random.uniform(item["ValueMin"], item["ValueMax"])

    def find_field_rule(self, item_type: str, field_name: str) -> dict:
        for field_rule in self.rules["Types"][item_type]["Fields"]:
            if field_rule["Field"] == field_name:
                return field_rule
        print("No rule for field " + field_name + " in type " + item_type)
        return {}

    def generate_json_template(self, output_filename="output/output-template.json"):
        self.dump_json(output_filename, template=True)

    def protocol_reduce(self, input_items: list) -> dict:
        output_items = {}
        for item in input_items:
            output_item_value = ""
            item_type = item["Type"]
            type_rule = self.rules["Types"][item_type]
            for field in item:
                if field == "Type":
                    continue
                field_rule = self.find_field_rule(item_type, field)
                if "GenerateCode" not in field_rule:
                    continue
                if field_rule["GenerateCode"]:
                    if type_rule["IsLeaf"] == True:
                        if field == "Key":
                            output_item_value = item["Key"]
                        else:
                            output_item_value = self.template_build_random_value(item)
                    elif field == "Items":
                        if item_type == "array":
                            if type(item["Items"]) is list:
                                output_item_value = ["" for _ in item["Items"]]
                            elif "Length" in item:
                                output_item_value = ["" for _ in range(item["Length"])]
                        else:
                            if (
                                len(item["Items"]) > 0
                                and type(item["Items"][0]) is dict
                            ):
                                output_item_value = self.protocol_reduce(item["Items"])
                            else:
                                print("Item " + item["Name"] + " has no items")
                    elif field == "data":
                        output_item_value = self.protocol_reduce(item["data"].copy())
                    break
            output_items[item["Name"]] = output_item_value
        return output_items

    def build_c_type(self, item: dict) -> str:
        type = item["metadata"]["Type"]
        if type == "Character":
            return "char *"
        elif type == "String":
            return "char *"
        elif type == "Integer":
            return "long *"
            output = ""
            number_of_states = (item["ValueMax"] - item["ValueMin"]) / item[
                "Resolution"
            ]
            is_signed = item["ValueMin"] < 0
            if number_of_states <= 256:
                output = "int8_t "
            elif number_of_states <= 65536:
                output = "int16_t "
            elif number_of_states <= 4294967296:
                output = "int32_t "
            else:
                output = "int64_t "
            if is_signed:
                return output
            else:
                return output.replace("int", "uint")
        elif type == "Float":
            return "double *"
        elif type == "List":
            return self.build_symbol_name(item, suffix="_t") + " *"
        elif type == "Dict":
            return self.build_symbol_name(item, suffix="_t") + " *"
        else:
            return "uint8_t "

    def _build_c_variable(self, item: dict) -> str:
        symbol_name = self.build_symbol_name(item)
        output = self.build_c_type(item) + symbol_name
        if item["metadata"]["Type"] == "array":
            output += "[" + str(len(item["data"])) + "];\n"
        else:
            output += ";\n"
        return output

    def build_c_structs(self, items: dict) -> str:
        output = ""
        typedef = ""
        for key, item in items.items():
            typedef = self.templates["typedef"]
            formatted_name = self.build_symbol_name(item)
            children_types = ""
            if item["metadata"]["Type"] == "Dict":
                output += self.build_c_structs(item["data"])
                for subitem in item["data"].values():
                    children_types += "    " + self._build_c_variable(subitem)
            elif item["metadata"]["Type"] == "List":
                for subitem in item["data"].values():
                    children_types += "    " + self._build_c_variable(subitem)
            else:
                continue
            output += (
                typedef.replace("<Name>", formatted_name)
                .replace("<Type>", item["metadata"]["Type"])
                .replace("<Key>", key)
                .replace("<Context>", item["metadata"]["Context"])
                .replace(
                    "<Description>",
                    item["metadata"]["Description"]
                    if "Description" in item["metadata"]
                    else "",
                )
                .replace("<CHILDREN_TYPES>", children_types.strip("\n"))
                + "\n"
            )
        return output

    def generate_c_header(self, output_filename="dd-protocol.h"):
        content = self.templates["header"].replace(
            "<TYPEDEFS>", self.build_c_structs(self.items)
        )
        with open(output_filename, "w") as outfile:
            outfile.write(content)

    def _generate_c_variable_declaration(
        self, item: dict, key: str, allocation: str
    ) -> str:
        output = ""
        children_types = ""
        children_objects = ""
        type = item["metadata"]["Type"]
        type_formated = "DD_TYPE_" + type.upper()
        formatted_name = self.build_symbol_name(item)

        if type == "Dict" or type == "List":
            output += (
                self.templates["object"]
                .replace("<Name>", formatted_name)
                .replace("<Allocation>", allocation)
                .replace("<Type>", type_formated)
                .replace("<Key>", key)
                .replace("<DataLength>", str(len(item["data"])))
            )
            for subitem in item["data"].values():
                formatted_subitem_name = self.build_symbol_name(subitem)
                children_types += (
                    "\t."
                    + formatted_subitem_name
                    + (" = " if subitem["metadata"]["Type"] == "String" else " = &")
                    + formatted_subitem_name
                    + ",\n"
                )
                children_objects += (
                    "\t" + self.build_symbol_name(subitem, suffix="_object") + ",\n"
                )
            output = output.replace("<CHILDREN_TYPES>", children_types.strip(",\n"))
            output = output.replace("<CHILDREN_OBJECTS>", children_objects.strip(",\n"))
        elif type == "String":
            output += (
                self.templates["string"]
                .replace("<Name>", formatted_name)
                .replace("<Allocation>", allocation)
                .replace("<Type>", type_formated)
                .replace("<Key>", key)
                .replace("<DataLength>", "64")
            )
        else:
            ctype = ""
            if type == "Integer":
                ctype = "long "
            elif type == "Float":
                ctype = "double "

            output += (
                (self.templates["leaftype"] + "\n" + self.templates["leafobject"])
                .replace("<Name>", formatted_name)
                .replace("<Allocation>", allocation)
                .replace("<Type>", type_formated)
                .replace("<Key>", key)
                .replace("<DataLength>", "0")
                .replace("<CTYPE>", ctype)
            )
        return output + "\n\n"

    def _generate_c_parser(self, item: dict, indent: int) -> tuple[str, str]:
        output = ""
        function_name = ""
        parsers = []
        if item["Type"] == "data":
            for subitem in item["data"]:
                parsers.append(self._generate_c_parser(subitem, indent))
        elif item["Type"] == "list":
            for subitem in item["Items"]:
                parsers.append(self._generate_c_parser(subitem, indent))
        elif item["Type"] == "array":
            output += "    " * indent + "}\n"
        else:
            parsers.append(
                ("    " * indent + item["Name"].replace(" ", "_") + " = ", "")
            )
        function_name = "parse_" + item["Name"].replace(" ", "_")
        output += (
            "int "
            + function_name
            + "(uint8_t *buffer, size_t len, "
            + item["Name"].replace(" ", "_")
            + "_t *"
            + item["Name"].replace(" ", "_")
            + ")\n{\n"
        )
        for parser in parsers:
            if parser[1] == "":
                output += parser[0] + ";\n"
                output += "    " * indent + "memcpy()"
            else:
                output += parser[1] + "()"
        return (output, function_name)

    def generate_c_functions(self, items: dict) -> str:
        output = self.templates["function"]
        output = output.replace("<Allocation>", "static").replace(
            "<ROOT_OBJECT>", list(items.keys())[0] + "_object"
        )
        return output

    def _generate_c_source(self, items: dict, allocation: str) -> str:
        output = ""
        for key, item in items.items():
            if item["metadata"]["Type"] == "Dict" or item["metadata"]["Type"] == "List":
                output += self._generate_c_source(item["data"], allocation)
            output += self._generate_c_variable_declaration(item, key, allocation)
        return output

    def generate_c_source(
        self, output_filename="dd-protocol.c", variable_allocation="static"
    ):
        with open(output_filename, "w") as outfile:
            outfile.write('#include "dd-protocol.h"\n')
            outfile.write("\n")
            outfile.write(self._generate_c_source(self.items, variable_allocation))
            outfile.write(self.generate_c_functions(self.items))


def main():
    parser = optparse.OptionParser(usage="usage: %prog [options]")
    parser.add_option(
        "-v",
        "--verbose",
        dest="verbose",
        help="enable verbose output",
        default=False,
        action="store_true",
    )
    parser.add_option(
        "-d",
        "--descriptor-file",
        dest="descriptor_file",
        type=str,
        help="YAML file with datagram description",
        metavar="DF",
    )
    parser.add_option(
        "-o",
        "--output-file",
        dest="output_file",
        type=str,
        default="output/dd-protocol",
        help="generated output file",
        metavar="FILE",
    )
    parser.add_option(
        "-r",
        "--input-rules",
        dest="input_rules",
        type=str,
        default="dd-rules.yaml",
        help="YAML file for datagram descriptor rules",
        metavar="RULES",
    )

    (options, args) = parser.parse_args()

    if options.descriptor_file is None:
        error("descriptor filename is required (use -d option)")

    CG = CodeGenerator(options.descriptor_file, branch_root="v3")
    if CG.datagram_is_valid:
        print("Datagram is valid - generating code")
        print("Generating JSON template...")
        CG.generate_json_template()
        print("Generating C header...")
        CG.generate_c_header(output_filename=options.output_file + ".h")
        print("Generating C source...")
        CG.generate_c_source(output_filename=options.output_file + ".c")
        print("Success!")
    else:
        print("Datagram is invalid - cannot generate code")


if __name__ == "__main__":
    main()
