# Python Functions

This repository contains a collection of Python functions designed to simplify common data wrangling tasks. These include renaming columns, moving columns, and replacing values in a DataFrame based on certain conditions.

## Installation

To install the dependencies for this project, use the following command:

\```
pip install -r requirements.txt
\```

Then, you can import the module in your Python script using:

\```python
import wrangling_functions as wf
\```

## Usage

### `rename_columns`

This function is used to rename columns in a DataFrame.

\```python
import pandas as pd
import wrangling_functions as wf

df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6],
    'C': [7, 8, 9]
})

old_names = ['A', 'B', 'C']
new_names = ['Column1', 'Column2', 'Column3']
df = wf.rename_columns(df, old_names, new_names)
print(df)
\```

**Output:**

\```
   Column1  Column2  Column3
0        1        4        7
1        2        5        8
2        3        6        9
\```

### `move_column`

This function moves a column in a DataFrame to a specified position.

\```python
import pandas as pd
import wrangling_functions as wf

df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6],
    'C': [7, 8, 9]
})

df = wf.move_column(df, 'A', 'first')
print(df)
\```

**Output:**

\```
   A  B  C
0  1  4  7
1  2  5  8
2  3  6  9
\```

### `simple_replace`

This function mimics Stata's replace command. It replaces values in a specific column of a DataFrame based on a certain condition.

\```python
import pandas as pd
import wrangling_functions as wf

df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6],
    'C': [7, 8, 9]
})

df = wf.simple_replace(df, 'B', 10, "A > 1")
print(df)
\```

**Output:**

\```
   A   B  C
0  1   4  7
1  2  10  8
2  3  10  9
\```

### `replace`

This function is a more advanced version of the `simple_replace` function. It allows you to specify a condition for the replacement operation and supports 'n' notation to indicate shift operation.

\```python
import pandas as pd
import wrangling_functions as wf

df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': ['cat', 'dog', 'mouse'],
    'C': [0.1, 0.3, -0.2],
    'D': pd.date_range('2023-01-01', periods=3)
})

condition = "(B == 'mouse') | (B[n-1] == 'dog') & (C[n+1] > -0.4)"
new_value = 'B[n+2]'
df_modified = wf.replace(df, 'A', condition, new_value)
print(df_modified)
\```

**Output:**

\```
     A      B    C          D
0  1.0    cat  0.1 2023-01-01
1  2.0    dog  0.3 2023-01-02
2  NaN  mouse -0.2 2023-01-03
\```

### `how_is_this_not_a_duplicate`

This function identifies columns that differ between the rows for a given combination of identifiers.

\```python
import pandas as pd
import wrangling_functions as wf

df = pd.DataFrame({
    'A': [1, 1, 3],
    'B': [4, 4, 6],
    'C': [7, 8, 9]
})

df = wf.how_is_this_not_a_duplicate(df, ['A', 'B'])
print(df)
\```

**Output:**

\```
   A  B  C
0  1  4  7
1  1  4  8
2  3  6  9
\```

### `bysort_sequence`

This function generates a sequence number (_n) or the maximum number (_N) within each group of the specified columns.

\```python
import pandas as pd
import wrangling_functions as wf

df = pd.DataFrame({
    'A': ['cat', 'dog', 'mouse'],
    'B': [1, 2, 3],
    'C': [4, 5, 6]
})

df = wf.bysort_sequence(df, ['A', 'B'], 'sequence')
print(df)
\```

**Output:**

\```
       A  B  C  sequence
0    cat  1  4         1
1    dog  2  5         1
2  mouse  3  6         1
\```

### `convert_to_units`

This is a helper function used to convert measurements to a different unit based on a conversion dictionary.

### `get_variable_names`

This function retrieves the names of variables of specified types.

\```python
x = 10
y = 'hello'
z = [1, 2, 3]
vars = wf.get_variable_names(int)
print(vars)
\```

**Output:**

\```
['x']
\```

### `count_occurrences_with_offset`

This function counts the occurrences of a given string in each row of a specified column, adds an offset, and appends the results as a new column.

\```python
import pandas as pd
import wrangling_functions as wf

df = pd.DataFrame({'instruments': ['Euphonium; Trombone', 'Trumpet', 'Percussion; Euphonium; Clarinet']})
df_new = wf.count_occurrences_with_offset(df, 'instruments', 'Euphonium', ';', 1)
print(df_new)
\```

**Output:**

\```
                           instruments  Euphonium_count
0                  Euphonium; Trombone               2
1                              Trumpet               1
2  Percussion; Euphonium; Clarinet     2
\```

### `create_top_charge`

This function creates a new column 'top_charge' in the dataframe.

\```python
df = pd.DataFrame({
    'Statute': ['Battery; Assault', 'Assault; Theft', 'Theft; Fraud'],
    'TotalCharges': [2, 2, 2],
    'Convicted': [1, 1, 0],
    'IncarcerationDays': [30, 10, 0],
    'Fine': [500, 200, 0]
})

df = wf.create_top_charge(df, 'Statute', 'TotalCharges', 'Convicted', 'IncarcerationDays', 'Fine')
print(df)
\```

**Output:**

\```
            Statute  TotalCharges  Convicted  IncarcerationDays  Fine top_charge
0  Battery; Assault             2          1                 30   500    Battery
1   Assault; Theft             2          1                 10   200    Assault
2      Theft; Fraud             2          0                  0     0      Theft
\```

### `recidivism`

This function calculates recidivism based on a given number of years and conviction status.

\```python
df = pd.DataFrame({
    'Date': pd.date_range('2023-01-01', periods=5),
    'PersonID': [1, 1, 2, 2, 2],
    'Convicted': ['Yes', 'No', 'Yes', 'Yes', 'No']
})

df = wf.recidivism(df, 'Date', 'PersonID', 1, only_convictions=True, conviction_col='Convicted', conviction_value='Yes')
print(df)
\```

**Output:**

\```
        Date  PersonID Convicted  recidivism
0 2023-01-01         1       Yes           0
1 2023-01-02         1        No           0
2 2023-01-03         2       Yes           0
3 2023-01-04         2       Yes           1
4 2023-01-05         2        No           1
\```

### `send_email_or_text`

This function sends an email or text message.

\```python
subject = "Hello"
body = "This is a test message."
sender = "sender@example.com"
recipients = ["recipient1@example.com", "recipient2@example.com"]
password = "password"
wf.send_email_or_text(subject, body, sender, recipients, password)
\```

**Output:**

\```
Message sent!
\```

### `find_and_highlight`

This function highlights a web element on a webpage. It temporarily changes the style of a web element to make it visually stand out.

\```python
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Firefox()
driver.get('http://www.python.org')
elem = driver.find_element(By.NAME, 'q')  # find the search box
wf.find_and_highlight(elem)  # highlight the search box
\```
