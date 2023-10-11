#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
This script builds an html files to be used in the reveal.js framework
to show slides. The input is one or many markup files.

General usage is:
makereveal.py -i <markup_file> -t <html_template> [ -o sildesfile.html ]

Parameters are:
-i <file>  The input file that contains the markdown. Slides are divided
           by a single line containing "---" and a linebeak. Also you may
           at metadata in the first block that is enclosed by the sepa-
           rator lines such as:
           ---
           title: my title for the slides
           description: some description
           author: Your Name
           ...
           ---
           This data is parsed as yaml and put into a key value pair so
           that inside a template the placeholder {{__key__}} is replaced
           with the value of that key in the header section. You can
           use whatever key you like, if there is a corresponding place-
           holder string in the template file, this content is written
           into the final output html.
--o <file> The html file where the compiled result is written to. This file
           can be placed into the root of the reveal.js projet at the same
           level where the index.html is located at.
           If an output file is not given, then the content is written to
           standard out. 
--t <file> The html template where the slides and the metadata are put into.
--help, -h Print this help information.

"""

import os, sys, re, yaml

usage = ("Usage: " + os.path.basename(sys.argv[0]) +
         " -i markup_file -t html_template ... [-o output_file]\n" +
         "Type --help for more details."
        )

def dieNice(errMsg = ""):
    print("Error: {0}\n{1}".format(errMsg, usage))
    sys.exit(1)


class MdParser:

    """
    MdParser that processes an markup file.
    """

    def __init__(self):

        self.files = []
        """ Store here the file name to read from."""

        self.properties = {}
        """A set of key values that are set from the head of the md file
        in case there is something set."""
        
        self._slides = []
        """A list of slides."""
        
        self._html = ''
        """The final HTML of the page, that is either written to stdout
        or into the output file"""
        
        self._slideDelimiter = re.compile('^\-{3}\r?\n$')
        """The delimiter to separate the slides and the yaml properties
        in the markdown file."""


    def addFile(self, file: str):
        """Add a file name to parse.

        Parameters:
        file (str): absolute file location.

        Returns:
        self:

        """
        self.files.append(file)
        return self


    def readFiles(self):
        """Read the markup files that were provided to the parser.

        Returns:
        self:

        """

        for fname in self.files:
            try:
                fp = open(fname, "r")
            except:
                dieNice('could not open file {0}'.format(fname))
            self.parseFile(fp)
            fp.close()
        return self

    def parseFile(self, fp: int):
        """Parse a single markup file.
        
        Parameters:
        fp (resource): pointer to the file to parse.
        
        Returns:
        self:
    
        """

        cnt = 0
        item = ''
        while line := fp.readline():
            if self._slideDelimiter.match(line):
                if cnt == 1:
                    try:
                        self.properties = yaml.safe_load(item)
                    except:
                        self._slides.append(item)
                    
                elif cnt > 1:
                    self._slides.append(item)
                cnt += 1
                item = ''
            else:
                item += line

        if len(item.replace("\r", '').replace('\n', '').strip()) > 0:
            self._slides.append(item)

        return self

    def replacePlaceholder(self, properties: dict, text: str)-> str:
        """Replace all placeholders with the given set of properties. Remove
        all placeholders that remain without replacement.
        
        Parameters:
        properties (dict): dictionary with key and replacement
        text (string): text with placeholders
        
        Returns:
        string: text with the subsituted replacements.
        """
    
        # Replace all property keys in the text.
        for key in properties:
            text = text.replace('{{__' + key + '__}}', str(properties[key]))
        # Replace all placeholders that didn't have a property set.
        text = re.sub(r'\{\{__\w+__\}\}', '', text)
        
        return text


    def getSlidesHtml(self)-> str:
        """Get the html content that is placed within the main part
        of the template where the slides are put into. Replace any
        {{__placeholder__}} pattern with what was defined in the
        properties.
        
        
        Returns:
        string: The html for the slides.
        """
        try:
            slides = list(map(lambda slide: self.replacePlaceholder(self.properties['template'], slide), self._slides))
        except KeyError:
            slides = list(map(lambda slide: self.replacePlaceholder({}, slide), self._slides))
        delimiters = ['<section data-markdown>\n<textarea data-template>\n', '</textarea>\n</section>\n']
        return delimiters[0] + (delimiters[1] + delimiters[0]).join(slides) + delimiters[1]

    def applyTemplate(self, template: str):
        """Apply the parsed data into a template file. The templace
        should have placeholders where the data from the markup file
        is placed into.
        
        Parameters:
        template (string): file name of the html template
        
        Returns:
        self:
        
        """

        try:
            fp = open(template, 'r')
        except:
            dieNice('Could not open template file ' + template)
        
        self._html = fp.read()
        fp.close()

        # Replace the slides placeholder with something else to prevend the elimination.
        self._html = self._html.replace('{{__slides__}}', '!###__slides__###!')

        self._html = self.replacePlaceholder(self.properties, self._html)
        
        # Now replace the slides placeholder with the real slides.
        self._html = self._html.replace('!###__slides__###!', self.getSlidesHtml())
        
        return self
        
    def getHtml(self)-> str:
        """Return the html of the final file
        
        Returns:
        string: The html of the entire file ready to use in reveal.js.
        """
        
        return self._html
                
def main():
    """Evaluate the cli arguments, built up the worklog object
    with the md files to be processed and build the tempate string
    for the html file."""

    # List of available options that can be changed via the command line.
    options = ['i', 'o', 't']

    # the output file where the result is written to, ready for use in reveal.js.
    outputFile = ''
    
    # the tempate file with the html.
    templateFile = ''

    # the worklog object that does the handling of the wiki articles.
    worklog = MdParser()

    # try to fetch the command line args
    currentCmd = ''
    for i in range(len(sys.argv)):
        if i == 0:
            continue
        arg = sys.argv[i]
        if arg == '--help' or arg == '-h':
            print(__doc__)
            sys.exit(0)
        if arg[0:1] == '-':
            currentCmd = arg[1:]
            if not(currentCmd in options):
                dieNice("Invalid argument %s" % currentCmd)
        elif len(currentCmd) > 0:
            if currentCmd == 'i':
                worklog.addFile(arg)
            elif currentCmd == 'o':
                outputFile = arg
            elif currentCmd == 't':
                templateFile = arg
            currentCmd = ''

    # process markup files
    worklog.readFiles()
    # apply the html template
    if len(templateFile) == 0 or not os.path.isfile(templateFile):
        dieNice('Template file missing or does not exist')
        
    content = worklog.applyTemplate(templateFile)

    # and output the result into the file
    try:
        if len(outputFile) == 0:
            fp = sys.stdout
        else:
            fp = open(outputFile, "w")
    except:
        dieNice('could not open file %s for writing result' % outputFile)

    fp.write(worklog.getHtml())
    fp.close()

if __name__ == "__main__":
    main()

