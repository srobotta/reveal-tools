#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
This script builds an html files to be used in the reveal.js framework
to show slides. The input is one or many markup files.

General usage is:
makereveal.py -i <markup_file> -t <html_template> [ -o sildesfile.html ]

Parameters are:
-c <theme> Select a Reveal theme, a corresponding file must exist in the
           reveal installation at css/theme/<theme>.css. Defaults to black.
-e         Do not copy any referenced files from the slides to the folder
           where the output file is created in.
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

import os, sys, shutil, re, yaml

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
        
        self.outFile = ''
        """ File where the output html is written to """
        
        self.properties = {}
        """A set of key values that are set from the head of the md file
        in case there is something set."""
        
        self.theme = 'black'
        """The theme name to be used in the reveal.js. This is actually the
        name of the css file (without the .css suffix) in
        reveal_root/css/theme."""

        self.skipExtFiles = False
        """Marker whether referenced files should be copied to the target
        directory"""
        
        self._slides = []
        """A list of slides."""
        
        self._html = ''
        """The final HTML of the page, that is either written to stdout
        or into the output file"""
        
        self._slideDelimiter = re.compile('^\-{3}\r?\n$')
        """The delimiter to separate the slides and the yaml properties
        in the markdown file."""
        
        self._externalFiles = {}
        """Store here the processed files, key is the origial file,
        value is the new file."""
        
        self._currentFileParsed = None


    def addFile(self, file: str):
        """Add a file name to parse.

        Parameters:
        file (str): absolute file location.

        Returns:
        self:

        """
        self.files.append(file)
        return self

    def setTheme(self, theme):
        """Set the reveal.js theme name and overwrite the default "black" theme.
        
        Parameters:
        theme (str): name of the theme
        
        Returns:
        self:
        """
        
        self.theme = theme
        return self

    def setDisableExternalFiles(self):
        """Disable that external files are not copied to the target directory.
        
        Returns:
        self:
        
        """
        
        self.skipExtFiles = True
        return self

    def setOutputFile(self, file: str):
        """Set the output file where the html is written to. If a directory
        is used, check that it exists.
        
        Parameters:
        file (str): file incl. path that is written.
        
        Returns:
        self:
        """
        self.outFile = file
        basedir = os.path.dirname(file)
        if basedir != '' and not os.path.exists(basedir):
            raise Exception('Directory "{0}" does not exist to write output file.'.format(basedir))
        return self

    def readFiles(self):
        """Read the markup files that were provided to the parser.

        Returns:
        self:

        """

        if len(self.files) == 0:
            dieNice('No input file provided.')

        for fname in self.files:
            try:
                fp = open(fname, "r")
            except:
                dieNice('Could not open file {0}.'.format(fname))
            self._currentFileParsed = fname
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
                item += self.checkForExternalFile(line)

        if len(item.replace("\r", '').replace('\n', '').strip()) > 0:
            self._slides.append(item)

        return self

    def checkForExternalFile(self, line: str)-> str:
        """Check for file patterns like:
        ![placeholder](external_file "placeholder tooltip")
        If something is found, check if the file exists, copy
        it to the current output dir and change the name and
        reference in the original markup."""
        
        # If we do not want to copy external files, just quit here.
        if self.skipExtFiles == True:
            return line
        
        # Check for occurrences of references to external files.
        for m in re.finditer('\[[^\]]*\]\(([^ \)]*)(\)| )', line):
            if m.group(1) in self._externalFiles.keys():
                line = line.replace(m.group(1), self._externalFiles[m.group(1)])
                continue
            
            basesrc = os.path.dirname(self._currentFileParsed)
            if basesrc != '':
                basesrc += os.sep
            # Check if the referenced file exists in relation to the markdown file where used.
            if not os.path.isfile(basesrc + m.group(1)):
                continue
            # Create the basename for the target file that is also used in the HTML.
            trg = ''.join([
                os.path.splitext(os.path.basename(m.group(1)))[0],
                '_',
                str(len(self._externalFiles) + 1),
                os.path.splitext(os.path.basename(m.group(1)))[1],
            ])
            self._externalFiles[m.group(1)] = trg
            # Copy source file to destination...
            basetrg = os.path.dirname(self.outFile)
            if basetrg != '':
                basetrg += os.sep
            shutil.copy(basesrc + m.group(1), basetrg + trg)
            # ... and replace the entry in the markup.
            replacement = m.group(0).replace(m.group(1), trg)
            line = line.replace(m.group(0), replacement)
        return line


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
            dieNice('Could not open template file "%s".' % template)
        
        self._html = fp.read()
        fp.close()

        # Replace the slides placeholder with something else to prevend the elimination.
        self._html = self._html.replace('{{__slides__}}', '!###__slides__###!')

        # Replace the theme name from the default or what was provided via cli argument.
        self._html = self._html.replace('{{__theme__}}', self.theme)

        # Replace all injected properties from the yaml header in the markup file(s).
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
        
    def writeOutput(self):
        """Write the resulting HTML into a file or on standard out.
        
        Returns:
        self:
        
        """

        try:
            if len(self.outFile) == 0:
                fp = sys.stdout
            else:
                fp = open(self.outFile, "w")
        except:
            dieNice('Could not open file %s for writing result.' % self.outFile)

        fp.write(self.getHtml())
        fp.close()
        return self
                
def main():
    """Evaluate the cli arguments, built up the worklog object
    with the md files to be processed and build the tempate string
    for the html file."""

    # List of available options that can be changed via the command line.
    options = ['c', 'e', 'i', 'o', 't']

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
                dieNice("Invalid argument %s." % currentCmd)
            if currentCmd == 'e':
                worklog.setDisableExternalFiles()
                currentCmd = ''
        elif len(currentCmd) > 0:
            if currentCmd == 'c':
                worklog.setTheme(arg)
            elif currentCmd == 'i':
                worklog.addFile(arg)
            elif currentCmd == 'o':
                try:
                    worklog.setOutputFile(arg)
                except Exception as ex:
                    dieNice(ex) 
            elif currentCmd == 't':
                templateFile = arg
            currentCmd = ''

    # Check if template file exists.
    if len(templateFile) == 0 or not os.path.isfile(templateFile):
        dieNice('Template file "{0}" missing or does not exist.'.format(templateFile))
    # process markup files
    worklog.readFiles()
    # apply the html template
    worklog.applyTemplate(templateFile).writeOutput()


if __name__ == "__main__":
    main()

