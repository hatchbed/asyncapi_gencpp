#!/usr/bin/env python3

# Copyright (c) 2022, Hatchbed
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse
import os
from re import sub
import sys
import textwrap
import yaml

typedefs = {}
components = {}


def upper_camel(name):
    name = sub(r"(_|-)+", " ", name)
    words = name.split(" ")
    words = list(map(lambda x: x[0].upper() + x[1:], words))
    return ''.join(words)


def snake_case(name):
    name = sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    name = sub('__([A-Z])', r'_\1', name)
    name = sub('([a-z0-9])([A-Z])', r'\1_\2', name)
    return name.lower()


def resolve_type(name):
    resolved = name
    while resolved in typedefs.keys():
        resolved = typedefs[resolved]
    return resolved


def resolve_definition(name, definition):
    resolved = name
    resolved_definition = definition

    if resolved in components.keys():
        resolved_definition = components[resolved]

    while resolved in typedefs.keys():
        resolved = typedefs[resolved]
        if resolved in components.keys():
            resolved_definition = components[resolved]

    return resolved_definition


def get_property_type(name, definition):
    cpp_type = None
    item_type = None

    if "type" not in definition:
        if "$ref" not in definition:
            return None, None
        cpp_type = upper_camel(definition["$ref"].split("/")[-1])
    if cpp_type is None:
        prop_type = definition["type"]
        if prop_type == "string":
            cpp_type = "std::string"
        elif prop_type == "integer":
            cpp_type = "int"
        elif prop_type == "number":
            cpp_type = "double"
        elif prop_type == "boolean":
            cpp_type = "bool"
        elif prop_type == "array":
            if "items" not in definition:
                return None, None
            if "$ref" in definition["items"]:
                item_type = upper_camel(definition["items"]["$ref"].split("/")[-1])
            elif "type" in definition["items"]:
                if definition["items"]["type"] == "string":
                    item_type = "std::string"
                elif definition["items"]["type"] == "integer":
                    item_type = "int"
                elif definition["items"]["type"] == "integer":
                    item_type = "int"
                elif definition["items"]["type"] == "boolean":
                    item_type = "bool"
                elif definition["items"]["type"] == "object":
                    item_type = upper_camel(name) + "Item"
            if item_type is None:
                return None, None
            cpp_type = "std::vector<{}>".format(item_type)
        elif prop_type == "object":
            cpp_type = upper_camel(name)

    return cpp_type, item_type


def init_typedefs(name, definition):
    class_name = upper_camel(name)
    base_type = None
    typedef = None
    if "schema" in definition:
        if "$ref" in definition["schema"]:
            typedef = upper_camel(definition["schema"]["$ref"].split("/")[-1])
        elif "type" in definition["schema"]:
            base_type = definition["schema"]
    if typedef is None and base_type is None and "type" in definition:
        base_type = definition
    if base_type is not None:
        if base_type["type"] == "string":
            typedef = "std::string"
        elif base_type["type"] == "integer":
            typedef = "int"
        elif base_type["type"] == "number":
            typedef = "double"
        elif base_type["type"] == "boolean":
            typedef = "bool"
        elif base_type["type"] == "array":
            # TODO
            pass
    if typedef is not None:
        typedefs[class_name] = typedef


def build_object(name, definition, prefix, all_required=False):
    headers = ["#include <memory>", "#include <optional>", "#include <string>"]
    lines = []
    required = []
    inner = []
    members = []
    properties = {}

    if "required" in definition:
        required = definition["required"]

    if "properties" in definition:
        properties = definition["properties"]

    for prop_name, prop_def in properties.items():
        prop_name_snake = snake_case(prop_name)
        prop_required = prop_name in required or all_required
        cpp_type = None
        item_type = None
        if "type" not in prop_def:
            if "$ref" not in prop_def:
                continue
            cpp_type = upper_camel(prop_def["$ref"].split("/")[-1])
            headers.append("#include <{}/{}.h>".format(prefix, cpp_type))
        if cpp_type is None:
            prop_type = prop_def["type"]
            if prop_type == "string":
                cpp_type = "std::string"
                headers.append("#include <string>")
            elif prop_type == "integer":
                cpp_type = "int"
            elif prop_type == "number":
                cpp_type = "double"
            elif prop_type == "boolean":
                cpp_type = "bool"
            elif prop_type == "array":
                if "items" not in prop_def:
                    continue
                if "$ref" in prop_def["items"]:
                    item_type = upper_camel(prop_def["items"]["$ref"].split("/")[-1])
                    headers.append("#include <{}/{}.h>".format(prefix, item_type))
                elif "type" in prop_def["items"]:
                    if prop_def["items"]["type"] == "string":
                        item_type = "std::string"
                        headers.append("#include <string>")
                    elif prop_def["items"]["type"] == "integer":
                        item_type = "int"
                    elif prop_def["items"]["type"] == "number":
                        item_type = "double"
                    elif prop_def["items"]["type"] == "boolean":
                        item_type = "bool"
                    elif prop_def["items"]["type"] == "object":
                        item_type = upper_camel(prop_name) + "Item"
                        sub_lines, sub_headers = build_object(item_type, prop_def["items"], prefix)
                        inner = inner + sub_lines
                        headers = headers + sub_headers
                if item_type is None:
                    continue
                headers.append("#include <vector>")
                cpp_type = "std::vector<{}>".format(item_type)
            elif prop_type == "object":
                cpp_type = upper_camel(prop_name)
                sub_lines, sub_headers = build_object(cpp_type, prop_def, prefix)
                sub_lines = list(map(lambda x: "  {}".format(x), sub_lines))
                inner = inner + sub_lines
                headers = headers + sub_headers

        if cpp_type is not None:
            if not prop_required and item_type is None:
                cpp_type = "std::optional<{}>".format(cpp_type)
            members.append("  {} {};".format(cpp_type, prop_name_snake))

    inner = list(map(lambda x: "  {}".format(x), inner))

    lines.append("struct {} {{".format(name))
    lines.append("    using Ptr = std::shared_ptr<{}>;".format(name))
    lines.append("    using ConstPtr = std::shared_ptr<const {}>;".format(name))
    lines = lines + inner
    lines = lines + members

    lines.append("")
    lines.append("  bool isValid() const {")

    for prop_name, prop_def in properties.items():
        prop_name_snake = snake_case(prop_name)
        prop_type, item_type = get_property_type(prop_name, prop_def)
        if prop_type is None:
            continue

        resolved_def = resolve_definition(prop_type, prop_def)
        prop_type = resolve_type(prop_type)
        if item_type is not None:
            item_def = resolve_definition(item_type, resolved_def["items"])
            item_type = resolve_type(item_type)
            conditions = []
            if item_type == "std::string":
                if "maxLength" in item_def:
                    conditions.append("      if (item.length() > {}) {{".format(item_def["maxLength"]))
                    conditions.append("        return false;")
                    conditions.append("      }")
                if "minLength" in item_def:
                    conditions.append("      if (item.length() < {}) {{".format(item_def["minLength"]))
                    conditions.append("        return false;")
                    conditions.append("      }")
                if "enum" in item_def:
                    conditions.append("      bool in_enum = false;")

                    if len(item_def["enum"]) > 0:
                        conditions.append('      if (item == "{}") {{'.format(item_def["enum"][0]))
                        conditions.append("        in_enum = true;")
                        conditions.append("      }")
                        for enum in item_def["enum"][1:]:
                            conditions.append('      else if (item == "{}") {{'.format(enum))
                            conditions.append("        in_enum = true;")
                            conditions.append("      }")
                    conditions.append("      if (!in_enum) {")
                    conditions.append("        return false;")
                    conditions.append("      }")
            elif item_type == "int" or item_type == "double":
                if "maximum" in item_def:
                    conditions.append("      if (item > {}) {{".format(item_def["maximum"]))
                    conditions.append("        return false;")
                    conditions.append("      }")
                if "minimum" in item_def:
                    conditions.append("      if (item < {}) {{".format(item_def["minimum"]))
                    conditions.append("        return false;")
                    conditions.append("      }")
            elif item_type == "bool":
                pass
            else:
                conditions.append("      if (!item.isValid()) {")
                conditions.append("        return false;")
                conditions.append("      }")
            if len(conditions) > 0:
                lines.append("    for (const auto& item: {}) {{".format(prop_name_snake))
                lines.extend(conditions)
                lines.append("    }")
        elif prop_name in required or all_required:
            if prop_type == "std::string":
                if "maxLength" in resolved_def:
                    lines.append("    if ({}.length() > {}) {{".format(prop_name_snake, resolved_def["maxLength"]))
                    lines.append("      return false;")
                    lines.append("    }")
                if "minLength" in resolved_def:
                    lines.append("    if ({}.length() < {}) {{".format(prop_name_snake, resolved_def["minLength"]))
                    lines.append("      return false;")
                    lines.append("    }")
                if "enum" in resolved_def:
                    lines.append("    bool _{}_in_enum = false;".format(prop_name_snake))

                    if len(resolved_def["enum"]) > 0:
                        lines.append('    if ({} == "{}") {{'.format(prop_name_snake, resolved_def["enum"][0]))
                        lines.append("      _{}_in_enum = true;".format(prop_name_snake))
                        lines.append("    }")
                        for enum in resolved_def["enum"][1:]:
                            lines.append('    else if ({} == "{}") {{'.format(prop_name_snake, enum))
                            lines.append("      _{}_in_enum = true;".format(prop_name_snake))
                            lines.append("    }")
                    lines.append("    if (!_{}_in_enum) {{".format(prop_name_snake))
                    lines.append("      return false;")
                    lines.append("    }")
            elif prop_type == "int" or prop_type == "double":
                if "maximum" in resolved_def:
                    lines.append("    if ({} > {}) {{".format(prop_name_snake, resolved_def["maximum"]))
                    lines.append("      return false;")
                    lines.append("    }")
                if "minimum" in resolved_def:
                    lines.append("    if ({} < {}) {{".format(prop_name_snake, resolved_def["minimum"]))
                    lines.append("      return false;")
                    lines.append("    }")
            elif prop_type == "bool":
                pass
            else:
                lines.append("    if (!{}.isValid()) {{".format(prop_name_snake))
                lines.append("      return false;")
                lines.append("    }")
        else:
            lines.append("    if ({}) {{".format(prop_name_snake))
            if prop_type == "std::string":
                if "maxLength" in resolved_def:
                    lines.append("      if ({}->length() > {}) {{".format(prop_name_snake, resolved_def["maxLength"]))
                    lines.append("        return false;")
                    lines.append("      }")
                if "minLength" in resolved_def:
                    lines.append("      if ({}->length() < {}) {{".format(prop_name_snake, resolved_def["minLength"]))
                    lines.append("        return false;")
                    lines.append("      }")
                if "enum" in resolved_def:
                    lines.append("      bool in_enum = false;")

                    if len(resolved_def["enum"]) > 0:
                        lines.append('      if (*{} == "{}") {{'.format(prop_name_snake, resolved_def["enum"][0]))
                        lines.append("        in_enum = true;")
                        lines.append("      }")
                        for enum in resolved_def["enum"][1:]:
                            lines.append('      else if (*{} == "{}") {{'.format(prop_name_snake, enum))
                            lines.append("        in_enum = true;")
                            lines.append("      }")
                    lines.append("      if (!in_enum) {")
                    lines.append("        return false;")
                    lines.append("      }")
            elif prop_type == "int" or prop_type == "double":
                if "maximum" in resolved_def:
                    lines.append("      if (*{} > {}) {{".format(prop_name_snake, resolved_def["maximum"]))
                    lines.append("        return false;")
                    lines.append("      }")
                if "minimum" in resolved_def:
                    lines.append("      if (*{} < {}) {{".format(prop_name_snake, resolved_def["minimum"]))
                    lines.append("        return false;")
                    lines.append("      }")
            elif prop_type == "bool":
                pass
            else:
                lines.append("      if (!{}->isValid()) {{".format(prop_name_snake))
                lines.append("        return false;")
                lines.append("      }")
            lines.append("    }")

    lines.append("    return true;")
    lines.append("  }")

    lines.append("")
    lines.append("  json toJson() const {")
    lines.append("    json j;")

    for prop_name, prop_def in properties.items():
        prop_name_snake = snake_case(prop_name)
        prop_type, item_type = get_property_type(prop_name, prop_def)
        if prop_type is None:
            continue

        prop_type = resolve_type(prop_type)
        if item_type is not None:
            item_type = resolve_type(item_type)
            lines.append("    json _{} = json::array();".format(prop_name_snake))
            lines.append("    for (const auto& item: {}) {{".format(prop_name_snake))
            if item_type == "std::string" or item_type == "int" or item_type == "double" or item_type == "bool":
                lines.append("      json json_item = item;")
            else:
                lines.append("      json json_item = item.toJson();")
            lines.append("      _{}.push_back(json_item);".format(prop_name_snake))
            lines.append("    }")
            lines.append('    j["{}"] = _{};'.format(prop_name, prop_name_snake))
        elif prop_name in required or all_required:
            if prop_type == "std::string" or prop_type == "int" or prop_type == "double" or prop_type == "bool":
                lines.append('    j["{}"] = {};'.format(prop_name, prop_name_snake))
            else:
                lines.append('    j["{}"] = {}.toJson();'.format(prop_name, prop_name_snake))
        else:
            lines.append("    if ({}) {{".format(prop_name_snake))
            if prop_type == "std::string" or prop_type == "int" or prop_type == "double" or prop_type == "bool":
                lines.append('      j["{}"] = *{};'.format(prop_name, prop_name_snake))
            else:
                lines.append('    j["{}"] = {}->toJson();'.format(prop_name, prop_name_snake))
            lines.append("    }")

    lines.append("    return j;")
    lines.append("  }")

    lines.append("")
    lines.append("  std::string dump(bool formatted=false) const {")
    lines.append("    auto j = toJson();")
    lines.append("    if (formatted) {")
    lines.append("      return j.dump(4);")
    lines.append("    }")
    lines.append("    else {")
    lines.append("      return j.dump();")
    lines.append("    }")
    lines.append("  }")

    lines.append("")
    lines.append("  static std::optional<{}> fromJson(const json& j) {{".format(name))
    lines.append("    {} _out;".format(name))

    for prop_name, prop_def in properties.items():
        prop_name_snake = snake_case(prop_name)
        prop_type, item_type = get_property_type(prop_name, prop_def)
        if prop_type is None:
            continue

        if prop_name in required or all_required:
            lines.append('    if (!j.contains("{}")) {{'.format(prop_name))
            lines.append("      return {};")
            lines.append("    }")
        else:
            lines.append('    if (!j.contains("{}")) {{'.format(prop_name))
            lines.append("      _out.{} = {{}};".format(prop_name_snake))
            lines.append("    }")
        lines.append("    else {")
        
        lines.append("      try {")

        if item_type is None:
            prop_type = resolve_type(prop_type)
            if prop_type == "std::string" or prop_type == "int" or prop_type == "double" or prop_type == "bool":
                lines.append('         _out.{} = j["{}"].get<{}>();'.format(prop_name_snake, prop_name, prop_type))
            else:
                lines.append('        auto _{} = {}::fromJson(j["{}"]);'.format(prop_name_snake, prop_type, prop_name))
                lines.append("        if (!_{}) {{".format(prop_name_snake))
                lines.append("          return {};")
                lines.append("        }")
                lines.append("        _out.{} = *_{};".format(prop_name_snake, prop_name_snake))
        else:
            item_type = resolve_type(item_type)
            lines.append('        if (!j["{}"].is_array()) {{'.format(prop_name))
            lines.append('          return {};')
            lines.append('        };')
            lines.append('        for (const auto& item: j["{}"]) {{'.format(prop_name))
            if item_type == "std::string":
                lines.append('          _out.{}.push_back(item.get<std::string>());'.format(prop_name_snake))
            elif item_type == "int":
                lines.append('          _out.{}.push_back(item.get<int>());'.format(prop_name_snake))
            elif item_type == "double":
                lines.append('          _out.{}.push_back(item.get<double>());'.format(prop_name_snake))
            elif item_type == "bool":
                lines.append('          _out.{}.push_back(item.get<bool>());'.format(prop_name_snake))
            else:
                lines.append('          auto _{}_item = {}::fromJson(item);'.format(prop_name_snake, item_type))
                lines.append("          if (!_{}_item) {{".format(prop_name_snake))
                lines.append("            return {};")
                lines.append("          }")
                lines.append("          _out.{}.push_back(*_{}_item);".format(prop_name_snake, prop_name_snake))
            lines.append('        }')

        lines.append("      }")
        lines.append("      catch (const std::runtime_error& error) {")
        lines.append("        return {};")
        lines.append("      }")

        lines.append("    }")

    lines.append("    return _out;")
    lines.append("  }")

    lines.append("")
    lines.append("  static std::optional<{}> fromJson(const std::string& s) {{".format(name))
    lines.append("    return fromJson(json::parse(s));")
    lines.append("  }")

    lines.append("};\n")
    return lines, list(set(headers))


def build_header(name, definition, prefix):

    description = ""
    if "summary" in definition:
        description = str(definition["summary"])

    if "description" in definition:
        if len(description) > 0:
            description = description + "\n"
        description = description + str(definition["description"])

    lines = []
    top_matter = []
    top_matter.append("#pragma once")
    top_matter.append("\n/* This file was auto-generated. */\n")
    headers = ["#include <nlohmann/json.hpp>"]

    lines.append("using json = nlohmann::json;")

    namespace = prefix.replace('/', '::')
    lines.append('namespace {} {{\n'.format(namespace))

    class_name = upper_camel(name)
    if len(description) > 0:
        description = '\n * '.join(textwrap.wrap(description, width=77, replace_whitespace=True))
        lines.append("/**")
        lines.append(" * {}".format(description))
        lines.append(" */")
    base_type = None
    typedef = None
    if "schema" in definition:
        if "$ref" in definition["schema"]:
            typedef = upper_camel(definition["schema"]["$ref"].split("/")[-1])
            headers.append("#include  <{}/{}.h>".format(prefix, typedef))
        elif "type" in definition["schema"]:
            base_type = definition["schema"]
    if typedef is None and base_type is None and "type" in definition:
        base_type = definition
    if base_type is not None:
        if base_type["type"] == "string":
            typedef = "std::string"
            headers.append("#include  <string>")
        elif base_type["type"] == "integer":
            typedef = "int"
        elif base_type["type"] == "number":
            typedef = "double"
        elif base_type["type"] == "boolean":
            typedef = "bool"
        elif base_type["type"] == "array":
            # TODO
            pass
    if typedef is not None:
        lines.append("typedef {} {};".format(typedef, class_name))
        typedefs[class_name] = typedef
    elif base_type is not None and base_type["type"] == "object":
        class_def, class_headers = build_object(class_name, base_type, prefix)
        lines = lines + class_def
        headers = headers + class_headers
    else:
        base_type = {'properties': definition}
        class_def, class_headers = build_object(class_name, base_type, prefix, all_required=True)
        lines = lines + class_def
        headers = headers + class_headers

    headers = list(set(headers))
    headers.sort()

    lines.append('}}  // namespace {}'.format(namespace))

    if len(headers) > 0:
        headers.append('')
        lines = headers + lines

    return top_matter + lines


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", help="AsyncAPI specification file")
    parser.add_argument("prefix", help="Include file prefix")
    parser.add_argument("outdir", help="Output directory")

    args = parser.parse_args()
    specfile = args.spec
    outdir = args.outdir

    if not os.path.exists(specfile):
        sys.exit('AsyncAPI specification file: [{}] does not exist'.format(specfile))

    if not os.path.isdir(outdir):
        sys.exit('Output directory: [{}] does not exist'.format(outdir))

    spec = None
    with open(specfile, "r") as f:
        try:
            spec = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            sys.exit('Failed to parse AsyncAPI specification file:\n{}'.format(exc))

    if "components" not in spec.keys():
        print("No components to generate.")
        sys.exit(0)

    schemas = {}
    if "schemas" in spec["components"]:
        schemas = spec["components"]["schemas"]

    if "messages" in spec["components"]:
        schemas.update(spec["components"]["messages"])

    prefix_dir = os.path.join(outdir, args.prefix)
    os.makedirs(prefix_dir, exist_ok=True)

    total_lines = 0

    # pre-initialize typedefs
    for name, definition in schemas.items():
        init_typedefs(name, definition)
        class_name = upper_camel(name)
        components[class_name] = definition

    # generate headers
    messages_header = []
    messages_header.append("#pragma once")
    messages_header.append("\n/* This file was auto-generated. */\n")
    for name, definition in schemas.items():
        header_src = build_header(name, definition, args.prefix)
        class_name = upper_camel(name)
        header_path = os.path.join(prefix_dir, class_name + ".h")
        messages_header.append("#include <" + args.prefix + "/" + class_name + ".h>")
        with open(header_path, 'w') as f:
            src = '\n'.join(header_src)
            f.write(src)
            length = len(src.splitlines())
            total_lines = total_lines + length
    total_lines = total_lines + len(messages_header)

    messages_header_path = os.path.join(prefix_dir, "messages.h")
    with open(messages_header_path, 'w') as f:
        f.write('\n'.join(messages_header))

    print("\n\n Total lines generated: {}".format(total_lines))
