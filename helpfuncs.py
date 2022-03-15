from typing import  List, Union

DATA_TYPES = ('TYPE_ACCELEROMETER',
              'TYPE_MAGNETIC_FIELD',
              'TYPE_GYROSCOPE',
              'TYPE_ROTATION_VECTOR',
              'TYPE_MAGNETIC_FIELD_UNCALIBRATED',
              'TYPE_GYROSCOPE_UNCALIBRATED',
              'TYPE_ACCELEROMETER_UNCALIBRATED',
              'TYPE_WIFI',
#               'TYPE_BEACON',
#               'TYPE_WAYPOINT'
              'TYPE_CHECKPOINT')




def count_header_row(content: List[str]) -> int:
    return min([i for i in range(len(content)) if not content[i].startswith('#')])


def separate_line_if_needed(line: str) -> list:
    '''Separate multiple data rows in a single file line.

    In path file, each single line expects to represent each single data row.
    Sometimes, however, a line dose not have the line feed at the end of itself,
    thus multiple data rows are belong to the line. This function will address
    such data quality problem.
    The function detects the problem by rough method. If line has greater than 
    10 columns, detect and try to address the problem. If not, treat it that 
    there are no data quality problem.

    Parameters
    ----------
    line: str
        Single line of sensor data file. It sometimes represents single data row,
        sometimes multiple.

    Return
    ------
    list of line(s): list
        If there are multiple data rows in line, separate it so that each line
        represents single data row. If not, return [list].
        
    Note
    ----
    This solution depends on that 1st column (Unix time) and 2nd column (data type)
    dose not have any quality problem such as missing value, invalid value,
    too long/short length, and so on.
    '''

    max_columns = 10
    field_sep = '\t'
    fields = [field for field in line.strip().split(field_sep)]
    idx_data_type = [i for i, field in enumerate(fields) if field in DATA_TYPES]
    if len(fields) <= max_columns:
        # No problem! line represents single record.
        return [line]

    """
    1. Identify where 1st row actually ends. The hint is where 2nd row's data type starts.
    2. Separate line into 2 parts; "1st row" and "Others".
    3. Add "1st row" of 2. to list of lines.
    4. Separate "Others" into single line(s) by same process recursively.
    """
    lines = []
    len_unix_time = 13  # Unix time milliseconds, such as '1560830841553'
    
    # 1.
    # where 2nd row's data type starts ?
    idx_second_data_type = idx_data_type[1]
    almost_first_row = field_sep.join(fields[:idx_second_data_type])  # 1st row + 2nd row's first column
    pos_first_row_end = len(almost_first_row) - len_unix_time  # Where 1st row actually ends
    # 2.
    first_row = line[:pos_first_row_end]
    others = line[pos_first_row_end:]
    # 3.
    lines.append(first_row)
    # 4.
    for l in others.splitlines():
        lines += separate_line_if_needed(l)

    return lines


def to_dict(header_or_footer: Union[str, list]) -> Union[None, dict]:
    '''Convert header/footer string into dictionary object.
    
    In path file, format of header and footer is described as follows;
    - header and footer line is starts with fixed string '#\t'
    - header and footer is composed of combinations of field name and value.
      i.e. '#\tSiteID:5cd56b83e2acfd2d33b5cab0\tSiteName:日月光中心'
    Field name and value is separated by generally ':'. Sometimes, however,
    they are separated by '\t'. This function addresses such inconsistent
    format problem partially.
    
    Parameters
    ----------
    header_or_footer: str or list
        header or footer represented by string, or list of them.
        
    Return
    ------
    dctionary or None:
        Return None if header_or_footer is actually a header/footer,
        otherwise dictionary (key: field name, value: field value).
    '''
    
    result_dict = {}
    if isinstance(header_or_footer, str):
        header_or_footer = [header_or_footer]
    
    header_or_footer = [l for l in header_or_footer if l.startswith('#\t')]
    if not header_or_footer:
        return None

    for line in header_or_footer:
        # We do not need First 3 chars '#\t" and line feed.
        fields = line[2:].strip().split('\t')
        skip = False
        for i, field in enumerate(fields):
            if skip:
                skip = False
                continue
            try:
                name, value = field.split(':')
            except ValueError:
                # Field name and value might be separated by "\t"
                name, value = fields[i], fields[i + 1]
                skip = True
            result_dict[name] = value
    return result_dict