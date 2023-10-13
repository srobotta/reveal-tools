# reveal-tools

Some tools to create presentations used with [reveal.js](https://revealjs.com/).

The motiviation was that I need to do a presentation and decided for reveal.js for
these reasons:
- I have a Linux running, no native Power Point
- I did not want to use the cloud version
- I have little knowledge in PP and the Libreoffice counterpart
- Focus on content rather tweaking the presentation layout and styling

Therefore the conclusion was reveal.js also because of a recomendation from a
collegue who uses that (in a greater stack) successfully.

For my personal use I setup a local reveal.js installation by doing the following:

1. Download the latest [reveal.js from github](https://github.com/hakimel/reveal.js/archive/master.zip)
1. Unzip the content into an arbitrary directory
1. Change into that directory and start a webserver by running `python3 -m http.server 8000`  

You can access the demo slides by calling http://localhost:3000/demo.html in your browser.


## makereveal.py

This script takes an markup file with slides as an input. Together with an html
template a ready to use html file for revealjs is created. It fits my needs but
can be further customized.

I could have used [pandoc](https://pandoc.org/) which at the long run might have
been a better solution however setup and fitting for my needs made me write this
python script.

### Usage

Usage is simple:
```
python3 makereveal.py -i slides.md -t template.html -o /path/to/reveal.js/out.html
```

The output file can be used in an installation of reveal.js in the root
directory where the index.html file is located.

### Markup file

The sildes are defined as markup (that may also contain html) in a single (or
several) markup files. The markup that can be used is defined by the reveal.js
plugin so details can be found there.

The separator for each slide in the markup file consists of three dashes followed
by a new line. At the moment the separator cannot be changed by a cli argument.

The markup file may have an optional header:
```
---
somekey: some value
[...]
template:
  tmplvar: some value that may contain html.
---
```

The header is treated as yml and in case it can be parsed, put into a dict
data type in python.
The first level element values (e.g. from somekey) will be inserted in the
html template where the place where the placeholder `{{__somekey__`}} is
used.

The key/value pairs below template can be used inside the markup file in the
slides. This is useful e.g. to have a larger html fragment defined above in
the header that is several times used in the slides.

All placeholders in the template that are not used will be removed. Encoding
e.g. use the correct html entites must be observed by the user, the script does
a simple replacement only.

There are two placeholders, that must be present in the template so that all
functionality works. These placeholders cannot be set via the yaml header
in the markup files. The special placeholders in the template are:

- `{{__slides__}}`: The slides from the markup are inserted here.
- `{{__theme__}}`: The theme name is put in here. This can be controlled via
the `-c` switch and defaults to "black".