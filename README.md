# Python-Functions
Custom libraries of custom python functions intended on making coding and wrangling easier. 

Consider these Beta versions. Use at your own risk.

Test cases for replace function:
```
df = pd.DataFrame({
    'A': [100, 200, 300, 400, 500],
    'B': [1, 2, np.nan, 4, 5],
    'C': ['test', np.nan, 'test2', 'test3', 'test4'],
    'D': ['longer string', 'short string', 'medium string', 'very long string', 'tiny']
})
```

### Test 1: Replace values in column 'A' where column 'B' is NaN with column 'C'
print(replace(df, 'A', 'B.isna', 'C'))

### Test 2: Replace values in column 'A' where column 'C' is not NaN with 'test'
print(replace(df, 'A', 'C.notna', 'test'))

### Test 3: Replace values in column 'A' where the length of column 'D' is greater than 10 with 'long'
print(replace(df, 'A', 'len(D) < 5', 'long'))

### Test 4: Replace values in column 'A' where column 'B' is NaN or the length of column 'D' is greater than 10 with 'mixed'
print(replace(df, 'A', 'B.isna | len(D) > 10', 'mixed'))
