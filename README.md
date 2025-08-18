NOTE: The code has grown much faster than the readme. Please be patient while I update the readme to reflect the current state of the code.

# Python Functions

This repository contains a collection of Python functions designed to simplify common data wrangling tasks. These include renaming columns, moving columns, and replacing values in a DataFrame based on certain conditions...

## Installation


This project has dependencies that are most easily installed using `conda`:

```bash
conda install -c conda-forge cartopy
```


To install the remaining dependencies for this project as well as the package itself, use the following command:

```shell
pip install git+https://github.com/robertpettis/pywrangling.git
```

or to upgrade:

```bash
pip install --upgrade git+https://github.com/robertpettis/pywrangling.git
```

or for a given branch, such as the experimental Beta branch:

```bash
pip install --upgrade git+https://github.com/robertpettis/pywrangling.git@Beta
```

or for a given tag, such as `2024-01-18`:
    
```bash
pip install --upgrade git+https://github.com/robertpettis/pywrangling.git@2024-01-18
```

or for a specific version, such as `0.39.2`:

```bash
pip install --upgrade git+https://github.com/robertpettis/pywrangling.git@0.39.2
```



Then, you can import the module in your Python script using:

## Usage

## wrangling_functions
```python
import pywrangling.wrangling_functions as wf
```

### `rename_columns`

This function serves the purpose of renaming columns within a DataFrame. While the functionality is similar to the existing method provided by pandas, some users may find this function preferable based on their personal coding style. This function addtionally adds the ability to add or remove suffixes, prefixes.

```python
import pandas as pd
import pywrangling.wrangling_functions as wf

df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6],
    'C': [7, 8, 9]
})

old_names = ['A', 'B', 'C']
new_names = ['Column1', 'Column2', 'Column3']
df = wf.rename_columns(df, old_names, new_names)
print(df)
```

**Output:**

```
   Column1  Column2  Column3
0        1        4        7
1        2        5        8
2        3        6        9
```

### `move_column`

This function moves a column in a DataFrame to a specified position.

Create the data:
```python
import pandas as pd
import pywrangling.wrangling_functions as wf

df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6],
    'C': [7, 8, 9]
})
```

Make the "B" column first. 
```
df = wf.move_column(df, 'B', 'first')
print(df)
```

**Output:**

```
   B  A  C
0  4  1  7
1  5  2  8
2  6  3  9
```

Make the "B" column the third column.
```
df = wf.move_column(df, 'B', 3)
print(df)
```

**Output:**

```
print(df)
   A  C  B
0  1  7  4
1  2  8  5
2  3  9  6
```

Return the "B" column to be after the "A" column.
```
df = wf.move_column(df, 'B', pos='after', ref_col="A")
print(df)
```

**Output:**

```
   A  B  C
0  1  4  7
1  2  5  8
2  3  6  9
```



### `replace`

This function intends to mimic Stata's replace function. It allows you to specify a condition for the replacement operation and supports 'n' notation to indicate shift operation.

```python
import pandas as pd
import pywrangling.wrangling_functions as wf

df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': ['cat', 'dog', 'mouse'],
    'C': [0.1, 0.3, -0.2],
    'D': pd.date_range('2023-01-01', periods=3)
})

condition = "(B == 'mouse') | (B[n-1] == 'dog') & (C[n+1] > -0.4)"
new_value = 'B[n-2]'
df_modified = wf.replace(df, 'A', condition, new_value)
print(df_modified)
```

**Output:**

```
     A      B    C          D
0  1.0    cat  0.1 2023-01-01
1  2.0    dog  0.3 2023-01-02
2  cat  mouse -0.2 2023-01-03
```

### `how_is_this_not_a_duplicate`

This function identifies columns that differ between the rows for a given combination of identifiers.

```python
import pandas as pd
import pywrangling.wrangling_functions as wf

df = pd.DataFrame({
    'A': [1, 1, 3],
    'B': [4, 4, 6],
    'C': [7, 8, 9],
    'D': [1, 2, 3],    
    
})

df = wf.how_is_this_not_a_duplicate(df, ['A', 'B'])
print(df)
```

**Output:**

```
   A  B  C  D problematic_cols
0  1  4  7  1             C, D
1  1  4  8  2             C, D
2  3  6  9  3              NaN
```

### `bysort_sequence`

This function generates a sequence number (_n) or the maximum number (_N) within each group of the specified columns.

```python
import pandas as pd
import pywrangling.wrangling_functions as wf

df = pd.DataFrame({
    'A': ['cat', 'cat', 'mouse'],
    'B': [2, 2, 3],
    'C': [4, 5, 6]
})

df = wf.bysort_sequence(df, ['A', 'B'], 'sequence')
print(df)
```

**Output:**

```
       A  B  C  sequence
0    cat  2  4         1
1    cat  2  5         2
2  mouse  3  6         1
```

### `convert_to_units`

This is a helper function used to convert measurements to a different unit based on a conversion dictionary.

### `count_occurrences_with_offset`

This function counts the occurrences of a given string in each row of a specified column, adds an offset, and appends the results as a new column.

```python
import pandas as pd
import pywrangling.wrangling_functions as wf

df = pd.DataFrame({'instruments': ['Euphonium; Trombone', 'Trumpet', 'Percussion; Euphonium; Clarinet']})
df_new = wf.count_occurrences_with_offset(df, 'instruments', 'Euphonium', ';', 1)
print(df_new)
```

**Output:**

```
                           instruments  Euphonium_count
0                  Euphonium; Trombone               2
1                              Trumpet               1
2  Percussion; Euphonium; Clarinet     2
```



## utility_functions
```python
import pywrangling.utility_functions as uf
```

### `send_email_or_text`

This function sends an email or text message. Note that, you may need to use an app password for your email account, not your usual password. 
Clarification is here, along with a link to google's gmail app password creation in the comments: https://stackoverflow.com/questions/70261815/smtplib-smtpauthenticationerror-534-b5-7-9-application-specific-password-req

```python
subject = "Hello"
body = "This is a test message."
sender = "sender@example.com"
recipients = ["recipient1@example.com", "recipient2@example.com"]
password = "password"
wf.send_email_or_text(subject, body, sender, recipients, password)
```

**Output:**

```
Message sent!
```

## scraping_functions
```python
import pywrangling.scraping_functions as cf
```

### `find_and_highlight`

This function highlights a web element on a webpage. It temporarily changes the style of a web element to make it visually stand out.

```python
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Firefox()
driver.get('http://www.python.org')
elem = driver.find_element(By.NAME, 'q')  # find the search box
wf.find_and_highlight(elem)  # highlight the search box
```
