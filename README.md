# Python Functions

This repository contains a collection of Python functions designed to simplify common data wrangling tasks. These include renaming columns, moving columns, and replacing values in a DataFrame based on certain conditions...

## Installation

To install the dependencies for this project, use the following command:

```shell
pip install git+https://github.com/robertpettis/pywrangling.git
```

or to upgrade:

```bash
pip install --upgrade git+https://github.com/robertpettis/pywrangling.git
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

```python
import pandas as pd
import pywrangling.wrangling_functions as wf

df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6],
    'C': [7, 8, 9]
})

df = wf.move_column(df, 'A', 'first')
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
    'C': [7, 8, 9]
})

df = wf.how_is_this_not_a_duplicate(df, ['A', 'B'])
print(df)
```

**Output:**

```
   A  B  C problematic_cols
0  1  4  7                C
1  1  4  8                C
2  3  6  9              NaN
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
0    cat  1  4         1
1    dog  2  5         2
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

## criminal_justice_functions
```python
import pywrangling.criminal_justice_functions as cf
```

### `create_top_charge`

This function creates a new column 'top_charge' in the dataframe. Note that the charges are determined based on their sentences when defendants have a single charge. 

```python
df = pd.DataFrame({
    'statute_col': ['Battery', 'Assault', 'Battery;Assault', 'Assault;Battery', 'Theft', 'Battery;Theft', 'Theft;Assault', 'Assault;Theft'],
    'total_charges_col': [1, 1, 2, 2, 1, 2, 2, 2],
    'convicted_col': [1, 1, 1, 1, 0, 1, 0, 1],
    'incarceration_days_col': [10, 20, 15, 25, 5, 30, 10, 40],
    'total_fine_col': [100, 200, 150, 250, 50, 300, 100, 400]
})

df = create_top_charge(df, 'statute_col', 'total_charges_col', 'convicted_col', 'incarceration_days_col', 'total_fine_col')
print(df)
```

**Output:**

```
statute_col	total_charges_col	convicted_col	incarceration_days_col	total_fine_col	top_charge
0	Battery	1	1	10	100	Battery
1	Assault	1	1	20	200	Assault
2	Battery;Assault	2	1	15	150	Assault
3	Assault;Battery	2	1	25	250	Assault
4	Theft	1	0	5	50	Theft
5	Battery;Theft	2	1	30	300	Battery
6	Theft;Assault	2	0	10	100	Assault
7	Assault;Theft	2	1	40	400	Assault
```

### `recidivism`

This function calculates recidivism based on a given number of years and conviction status.

```python
df = pd.DataFrame({
    'Date': pd.date_range('2023-01-01', periods=5),
    'PersonID': [1, 1, 2, 2, 2],
    'Convicted': ['Yes', 'No', 'Yes', 'Yes', 'No']
})

df = wf.recidivism(df, 'Date', 'PersonID', 1, only_convictions=True, conviction_col='Convicted', conviction_value='Yes')
print(df)
```

**Output:**

```
        Date  PersonID Convicted  recidivism
0 2023-01-01         1       Yes           0
1 2023-01-02         1        No           0
2 2023-01-03         2       Yes           0
3 2023-01-04         2       Yes           1
4 2023-01-05         2        No           1
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

## scrapinge_functions
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
