# AutoOED Documentation

This is the documentation folder of AutoOED which is built with [Sphinx](https://www.sphinx-doc.org/) using a [theme](https://github.com/readthedocs/sphinx_rtd_theme) provided by [Read the Docs](https://readthedocs.org/).

## Compile Locally

To see the documentation locally as an interactive website, do the following steps:

1. Install python dependencies:
    ```
    pip install sphinx sphinx_rtd_theme recommonmark
    ```


2. Compile at the current directory:

   ```
   make html
   ```

3. See the compiled documentation at: *build/html/index.html*

## Update Content

To update writing content of the documentation, navigate to *source/content/* folder and find the corresponding file. This content folder is organized according to the hierarchy of the documentation, which can be found and updated in *source/index.rst*. 

The content files are written in [reStructuredText](https://docutils.sourceforge.io/rst.html) (.rst). Here are some tutorials and examples of how to write .rst files if you are not familiar with it:

- https://docutils.sourceforge.io/docs/user/rst/quickref.html
- https://docs.anaconda.com/restructuredtext/detailed/
- https://github.com/readthedocs/readthedocs.org/blob/master/docs/intro/getting-started-with-sphinx.rst (click "raw" button to see the raw .rst file content)

