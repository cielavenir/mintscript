#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Replacement of enscript using XeLaTeX and minted
'''

import argparse
import contextlib
import logging
import os
import shutil
import subprocess
import tempfile
import sys

from enscript import parseargs, parseformat, parsefont
from latex import latexoptions, buildlatex

@contextlib.contextmanager
def cd(newdir, cleanup=lambda: True):
    '''change the current working directory and yield. Upon context close, goes
    back to the original directory and execute the clean up function.

    Args:
        newdir (str): path to new working dir, ~username supported
        cleanup (callable): will execute this upon context close
    '''
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)
        cleanup()

@contextlib.contextmanager
def tempdir():
    '''a context manager to create a temp dir and change the working directory
    to it. Useful for learning up after running code that generate files in the
    local dir.
    '''
    dirpath = tempfile.mkdtemp()
    def cleanup():
        shutil.rmtree(dirpath)
    with cd(dirpath, cleanup):
        yield dirpath

def main():
    args = parseargs()
    if len(args.file) < 1:
        logging.error('stdin entry is not yet supported')
        sys.exit(1)
    logging.getLogger('').setLevel(logging.ERROR if args.quiet else logging.DEBUG)
    options = latexoptions(args)
    logging.debug(options)
    files = ["source%d%s"%(i, os.path.splitext(f)[-1]) for i,f in enumerate(args.file)]
    latexcode = buildlatex(options, files)
    texfile = 'mintscript.tex'
    pdffile = texfile[:-3] + 'pdf'
    cwd = os.getcwd()
    with tempdir() as _:
        for oldpath,newpath in zip(args.file, files):
            oldpath = os.path.join(cwd, oldpath)
            if not os.path.isfile(oldpath):
                logging.error('Cannot read file %s' % oldpath)
                sys.exit(1)
            shutil.copyfile(oldpath, newpath)
            logging.debug('Copied %s to %s' % (oldpath, newpath))
        assert(texfile not in files)
        with open(texfile,'w') as fp:
            fp.write(latexcode)
        logging.debug('LaTeX code:\n%s' % latexcode)
        commandline = ['xelatex','-shell-escape','-batch',texfile]
        for i in range(2): # run latex twice due to labels
            status = subprocess.call(commandline)
            if status != 0:
                logging.error('xelatex failed with return code %s' % status)
                sys.exit(status)
        if not os.path.isfile(pdffile):
            logging.error('xelatex completed but %s not found in output' % pdffile)
            sys.exit(1)
        if not args.output:
            args.output = os.path.splitext(args.file[0])[0] + '.pdf'
        logging.debug('Output to %s' % args.output)
        if args.output == '-':
            sys.stdout.buffer.write(open(pdffile).read()) # dump binary to stdout
        elif args.output:
            shutil.copyfile(pdffile, os.path.join(cwd,args.output))

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s:%(name)s(%(lineno)d):%(levelname)s:%(message)s')
    main()

# vim:set et sw=4 ts=4:
