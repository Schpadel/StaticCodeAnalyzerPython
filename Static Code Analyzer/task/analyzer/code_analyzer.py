import operator
import os
import re
import sys
from pathlib import Path
import ast

arguments = sys.argv
file_path = arguments[1]
current_file = file_path
counter = 1
count_blank = 0
already_found = False


def append_message(code, message, messages, line_number):
    global current_file
    messages.append((("{}: Line {}: {} {}".format(current_file, line_number, code, message)), code, line_number))


def check_s001():
    global code, message, messages
    if len(line) > 79:
        code = "S001"
        message = "Too long"
        append_message(code, message, messages, counter)


def check_s005():
    global code, message, messages
    if ("#" in line and "TODO" in line) or ("#" in line and "todo" in line.lower()):
        code = "S005"
        message = "TODO found"
        append_message(code, message, messages, counter)


def check_s004():
    global code, message
    if "#" in line:
        temp_lines = line.split("#")
        code_line = temp_lines[0]

        if code_line != "":
            if code_line[-1] != " " or code_line[-2] != " ":
                code = "S004"
                message = "At least two spaces required before inline comments"
                append_message(code, message, messages, counter)


def check_s003():
    local_code = "S003"
    local_message = "Unnecessary semicolon after a statement"
    if len(line) > 0:
        if line.count('"') > 0 or line.count("'") > 0:
            new_line = re.sub(r'".+?"', '', line)
            new_line = re.sub(r"'.+?'", '', new_line)
        else:
            new_line = line

        if new_line.count("#") == 0 and new_line[-1] == ";":
            append_message(local_code, local_message, messages, counter)
        else:
            temp_lines = new_line.split("#")
            if temp_lines[0].count(";") > 0:
                append_message(local_code, local_message, messages, counter)


def check_s006():
    global code, message, count_blank, already_found, counter

    if count_blank > 2 and line != "" and already_found:
        code = "S006"
        message = "More than two blank lines preceding a code line"
        append_message(code, message, messages, counter)

    if line == "\n" or line == "":
        count_blank = count_blank + 1
    else:
        already_found = False
        count_blank = 0

    if count_blank > 2 and (line == "\n" or line == "") and not already_found:
        already_found = True


def check_s007():
    template_error = r"\s*def[ ]{2,}\w|\s*class[ ]{2,}\w"
    if re.match(template_error, line):
        found_error = "not found"
        class_or_def = re.search(r"\s\w+ ", line)
        if class_or_def:
            found_error = class_or_def.group(0)
        append_message("S007", "Too many spaces after{}".format(found_error), messages, counter)


def check_s008():
    class_name = "Not found!"
    template_error = r"\s*class [a-z]+"
    if re.match(template_error, line):
        class_name = re.search(r"\s[a-z]*", line)
        if class_name:
            class_name = class_name.group(0)
        append_message("S008", "Class name{} should use CamelCase".format(class_name), messages, counter)


def check_s009():
    function_name = "Not found!"
    template_error = r"\s*def [A-Z]+"
    if re.match(template_error, line):
        function_name = re.search(r"\s[A-Z]*[a-z]*", line)
        if function_name:
            function_name = function_name.group(0)
        append_message("S009", "Function name{} should use snake_case".format(function_name), messages, counter)


def check_s010():
    for node in ast.walk(syntax_tree):
        if isinstance(node, ast.FunctionDef):
            func_args = node.args
            template_error = r"\s*[A-Z]+"
            for a in func_args.args:
                if re.match(template_error, a.arg):
                    append_message("S010", "Argument name {} should be written in snake_case".format(a.arg), messages,
                                   node.lineno)


def check_s011():
    template_error = r"\s*[A-Z]+"
    for node in ast.walk(syntax_tree):
        if isinstance(node, ast.Name):

            var_name = node
            if isinstance(var_name.ctx, ast.Store):
                # check if var fulfills snake_case -> raise error message if not
                if re.match(template_error, var_name.id):
                    append_message("S011", "Variable {} should be written in snake_case".format(var_name.id), messages,
                                   node.lineno)


def check_s012():
    template_error = r"[]|{}"
    for node in ast.walk(syntax_tree):
        if isinstance(node, ast.FunctionDef):
            func_defaults = node.args.defaults
            for default_arg in func_defaults:
                if isinstance(default_arg, ast.List) or isinstance(default_arg, ast.Dict) or isinstance(default_arg, ast.Set):
                #if re.match(template_error, default_arg):
                    append_message("S012", "The default argument value is mutable", messages, node.lineno)




def error_code(elem):
    return [elem[2], elem[1]]


def check_s002():
    global code, message, messages

    if len(line) == 0:
        return

    i = 0
    while line[i] == " ":
        i = i + 1
    if i % 4 != 0:
        append_message("S002", "Indentation is not multiple of four", messages)


file_or_dir = Path(file_path)

if file_or_dir.is_dir():
    with os.scandir(file_path) as entries:
        for entry in entries:
            if ".py" in entry.name:

                with open(entry, "r") as file_to_analyze:
                    current_file = file_to_analyze.name
                    messages = list()
                    file_string = file_to_analyze.read()
                    syntax_tree = ast.parse(file_string)

                    check_s010()
                    check_s011()
                    check_s012()

                    file_string = file_string.split("\n")
                    counter = 1

                    for line in file_string:
                        check_s001()
                        check_s002()
                        check_s005()
                        check_s004()
                        check_s003()
                        check_s006()
                        check_s007()
                        check_s008()
                        check_s009()

                        counter = counter + 1

                    messages.sort(key=error_code)
                    for output in messages:
                        print(output[0])
                    messages.clear()


elif file_or_dir.is_file():
    with open(file_or_dir, "r") as file_to_analyze:
        current_file = file_to_analyze.name
        file_string = file_to_analyze.read()
        syntax_tree = ast.parse(file_string)
        messages = list()

        check_s010()
        check_s011()
        check_s012()

        file_string = file_string.split("\n")
        counter = 1


        for line in file_string:
            check_s001()
            check_s002()
            check_s005()
            check_s004()
            check_s003()
            check_s006()
            check_s007()
            check_s008()
            check_s009()

            counter = counter + 1

        messages.sort(key=error_code)
        for output in messages:
            print(output[0])
        messages.clear()

else:
    print("Error input is neither file or directory!")
