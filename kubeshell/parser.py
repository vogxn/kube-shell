import json
import os


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


class Parser(object):
    """ Parser builds and walks the syntax tree of kubectl """

    def __init__(self, apiFile):
        self.json_api = apiFile
        self.schema = dict()
        with open(self.json_api) as api:
            self.schema = json.load(api)
        self.ast = CommandTree("kubectl")
        self.build(self.ast, self.schema.get("kubectl"))

    def build(self, root, schema):
        """ Build the syntax tree for kubectl command line """
        if schema.get("subcommands") and schema["subcommands"]:
            for subcmd, childSchema in schema["subcommands"].items():
                child = CommandTree(node=subcmd)
                root.children.append(child)
                self.build(child, childSchema)
        else:
            # {args: {}, options: {}, help: ""}
            root.helptext = schema.get("help")

            for name, desc in schema.get("options").items():
                root.localFlags.append(Option(name, desc["help"]))

            for arg in schema.get("args"):
                node = CommandTree(node=arg)
                root.children.append(node)

    def parse_tokens(self, tokens):
        """ Parse a sequence of tokens

        returns tuple of (parsed tokens, suggestions)
        """
        if len(tokens) == 1:
            return list(), ["kubectl"]
        else:
            tokens.reverse()
            tokens.pop()
        parsed, suggestions = self.treewalk(self.ast, parsed=["kubectl"], unparsed=tokens)
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
            # elif token.startswith("--"):
            #     for flag in root.localFlags:
            #         if flag == token:
            #             parsed.append(token)
            #             self.treewalk()
            else:
                unparsed.append(token)
                suggestions = list()
                for child in root.children:
                    suggestions.append(child.node)
                return parsed, suggestions
        return parsed, list()


if __name__ == '__main__':
    Parser('data/cli.json')
