#!/usr/bin/env python3

import sys
import fnmatch
import os
import ast

# words that indicate that something is not really a comment
reserved = {'pylint', 'pragma'}

def get_comment(line):
    """
    Get a comment from a line of code or return False
    """
    quotation = {'"', "'"}
    if '#' not in line:
        return False
    first, second = line.split('#', 1) # HARDEST TO GET
    second = second.strip()
    if not first:
        return second

    if not second:
        return False

    # if it is not possible that the hash symbol is inside a string
    first_has_quote = any(i in first for i in quotation)
    second_has_quote = any(i in second for i in quotation) # on the end of a line
    # cannot be a string if no quotation mark somewhere before it
    if not first_has_quote:
        return second

    if first_has_quote and second_has_quote:
        # in this case, we don't know if the hash was in a string, so try again
        return get_comment(second)

    if not any(x.isalpha() for x in second):
        return False

    return second

def is_valid_python(code):
    """
    Check if code is calid Python, though imperfectly. Used to filter out
    code that has been commented out
    """
    try:
        ast.parse(code)
    except SyntaxError:
        return False
    return True

def get_comments(data, allow_single_word=True):
    """
    Extract comments from Python file, including multiline comments
    """
    comments = []
    skippable = set()
    data = data.splitlines()
    for i, line in enumerate(data):
        x = 1
        comment = get_comment(line)
        if not comment or not i:
            continue
        hash_index = line.index('#')
        try:
            next_line = data[i+x]
        except IndexError:
            break
        long_enough = len(next_line) > hash_index
        same_column = next_line[hash_index] == '#' if long_enough else False
        while '#' in next_line and long_enough and same_column:
            extra_comment = get_comment(next_line)
            if not extra_comment:
                break
            comment += ' ' + extra_comment
            skippable.add(i+x)
            x += 1
            try:
                next_line = data[i+x]
            except IndexError:
                break

        if any(i in comment for i in reserved):
            continue

        comment = comment.strip().replace('\n', ' ').replace('\r', '')
        if not is_valid_python(comment) and any(i.isalpha() for i in comment):
            # if multiple words, let's make it a sentence for our parser.
            if ' ' in comment:
                comment = comment.rstrip('.') + '.'
            else:
                if not allow_single_word:
                    continue
            comments.append(comment)
    return comments

def get_docstrings(data):
    """
    Here is a docstring over in this file
    over multiple lines
    """
    docstrings = []
    code = ast.parse(data)
    for node in ast.walk(code):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
            docstring = ast.get_docstring(node)
            if docstring:
                docstrings.append(docstring.replace('\n', ' '))
    return docstrings

def run(fpath, output='corpus.txt'):
    """
    Main method: iterate over all files in
    """
    filepaths = set()
    forms = []
    # one comment here
    for root, dirnames, filenames in os.walk(fpath):
        for filename in fnmatch.filter(filenames, '*.py'):
            filepaths.add(os.path.join(root, filename))

    for i, filepath in enumerate(sorted(filepaths), start=1):
        print('Doing {}/{}'.format(i, len(filepaths)))
        with open(filepath, 'r') as fo:
            data = fo.read()
        comments = get_comments(data)
        #docstrings = get_docstrings(data)
        docstrings = []
        formatted = '\n'.join(comments) + '\n' + '\n'.join(docstrings)
        formatted = formatted.replace('\n\n', '\n')
        forms.append(formatted)

    with open(output, 'w') as fo:
        fo.write('\n'.join(forms) + '\n')

if __name__ == '__main__':
    fpath = sys.argv[-1] if os.path.isdir(sys.argv[-1]) else '.'
    run(fpath)
