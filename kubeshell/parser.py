import json
import os
import logging

logger = logging.getLogger("kubeshell.logger")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler("kubeshell.log")
FORMAT = "%(asctime)s %(levelname)-8s %(funcName)s:%(lineno)s %(message)s"
formatter = logging.Formatter(fmt=FORMAT)
handler.setFormatter(formatter)
logger.addHandler(handler)

class Option(object):
    """ Option represents an optional local flag in kubectl """

    def __init__(self, name, helptext):
        self.name = name
        self.helptext = helptext


class CommandTree(object):
    """ CommandTree represents the tree node of a kubectl command line """

    def __init__(self, node=None, helptext=None, children=None, localFlags=None):
        self.node = node
        self.help = helptext
        self.children = children if children else list()
        self.localFlags = localFlags if localFlags else list()

    def __str__(self):
        return "Node: %s, Help: %s\n Flags: %s\n Children: %s" % (self.node, self.help, self.localFlags, self.children)


class Parser(object):
    """ Parser builds and walks the syntax tree of kubectl """

    def __init__(self, apiFile):
        self.json_api = apiFile
        self.schema = dict()
        with open(self.json_api) as api:
            self.schema = json.load(api)
        self.ast = CommandTree("kubectl")
        self.ast = self.build(self.ast, self.schema.get("kubectl"))

    def build(self, root, schema):
        """ Build the syntax tree for kubectl command line """
        if schema.get("subcommands") and schema["subcommands"]:
            for subcmd, childSchema in schema["subcommands"].items():
                child = CommandTree(node=subcmd)
                child = self.build(child, childSchema)
                root.children.append(child)
        # {args: {}, options: {}, help: ""}
        root.help = schema.get("help")
        for name, desc in schema.get("options").items():
            root.localFlags.append(Option(name, desc["help"]))
        for arg in schema.get("args"):
            node = CommandTree(node=arg)
            root.children.append(node)
        return root

    def print_tree(self, root, indent=0):
        indentter = '{:>{width}}'.format(root.node, width=indent)
        print(indentter)
        for child in root.children:
            self.print_tree(root=child, indent=indent+2)

    def parse_tokens(self, tokens):
        """ Parse a sequence of tokens

        returns tuple of (parsed tokens, suggestions)
        """
        if len(tokens) == 1:
            return list(), ["kubectl"]
        else:
            tokens.reverse()
        parsed, unparsed, suggestions = self.treewalk(self.ast, parsed=[], unparsed=tokens)
        return parsed, suggestions

    def treewalk(self, root, parsed, unparsed):
        """ Walk the syntax tree at root

        return tuple of tokens parsed and possible suggestions """
        if unparsed:
            token = unparsed.pop().strip()
            if root.node == token:
                parsed.append(token)
                for child in root.children:
                    self.treewalk(child, parsed, unparsed)
                suggestions = list()
                for child in root.children:
                    suggestions.append(child.node)
                return parsed, unparsed, suggestions
            # elif token.startswith("--"):
            #     for flag in root.localFlags:
            #         if flag == token:
            #             parsed.append(token)
            #             self.treewalk()
            else:
                unparsed.append(token)
        return parsed, unparsed, None

if __name__ == '__main__':
    Parser('data/cli.json')
