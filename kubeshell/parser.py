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
            return list(), {"kubectl": self.ast.help}
        else:
            tokens.reverse()
        parsed, _, suggestions = self.treewalk(self.ast, parsed=list(), unparsed=tokens)
        return parsed, suggestions

    def treewalk(self, root, parsed, unparsed):
        """ Recrusively walks the syntax tree at root and returns
        the items parsed, unparsed and possible suggestions """
        suggestions = dict()
        if not unparsed:
            return parsed, unparsed, suggestions

        token = unparsed.pop().strip()
        if root.node == token:
            parsed.append(token)
            if self.isOption(unparsed):
                return self.evalOptions(root, parsed, unparsed[:])
            for child in root.children:
                # recursively walk children of matched node
                child_parsed, unparsed, suggestions = self.treewalk(child, list(), unparsed[:])
                if child_parsed:  # subtree returned further parsed tokens
                    parsed.extend(child_parsed)
                    break
            else:
                # no matches found in command tree
                # return children of root as suggestions
                for child in root.children:
                    suggestions[child.node] = child.help
            return parsed, unparsed, suggestions
        else:
            unparsed.append(token)
        return parsed, unparsed, suggestions

    def isOption(self, unparsed):
        """ Peek to find out if next token is an option """
        if unparsed and unparsed[0].startswith("--"):
            return True
        return False

    def evalOptions(self, root, parsed, unparsed):
        """ Evaluate only the options and return flags as suggestions """
        if not self.isOption(unparsed):
            return parsed, unparsed, dict()
        suggestions = dict()
        nextToken = unparsed.pop()
        for flag in root.localFlags:
            if flag.name == nextToken:
                parsed.append(nextToken)
                break
        else:
            for flag in root.localFlags:
                suggestions[flag.name] = flag.helptext
        return parsed, unparsed, suggestions
