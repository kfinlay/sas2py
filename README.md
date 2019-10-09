# SAS2PY

Python utilities to extract data from SAS

## Requirements
This program makes calls to SAS, so you need a SAS executable installed/on your PATH.

## Usage

### To convert a .sas7bdat file to .csv
```
from sas2py import sas2py
sas2py.sas2csv("input_file.sas", "output_file.csv", "logdir_for_sas")
```

## Acknowledgements

 - [inlinesas](https://github.com/wharton/inlinesas)
