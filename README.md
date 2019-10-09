# SAS2PY

Python utilities to extract data from SAS

The SAS7BDAT data file format is closed-source. If you work with legacy SAS data, you might find that open-source SAS parsers, such as the pandas read_sas/SAS7BDATReader, are not able to convert some SAS7BDAT files. This project includes scripts for accessing SAS7BDAT data and metadata using the SAS executable.

## Requirements

This program makes calls to SAS, so you need a SAS executable installed/on your PATH.

## Usage

### To convert a .sas7bdat file to .csv

```
from sas2py import sas2py
sas2py.sas2csv('input_file.sas7bdat', 'output_file.csv', 'logdir_for_sas')
```

### To extract file and variable metadata from a .sas7bdat file

```
(datasetMetaDict, variableMetaList) = exportSASMetadata('input_file.sas7bdat', 'tempdir_for_sas')
```

### To calculate the most frequent values for a single variable in a .sas7bdat file

```
vals_list = sasSQLVarMostFreq('input_file.sas7bdat', 'varname', 'tempdir_for_sas')
```

## Acknowledgements

 - [inlinesas](https://github.com/wharton/inlinesas)
