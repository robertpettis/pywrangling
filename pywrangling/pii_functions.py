
# %% Import Packages
import random  # To generate random numbers
import re  # Regular expressions library for string manipulation
import string  # For alphabet string manipulation

# %% Functions

import random
import string
import re

def depersonalize(data, seed=None):
    """
    Depersonalize data by shifting letters and adding an offset to digits based on the seed.

    Parameters:
    data (str): The data to be depersonalized.
    seed (int, optional): A seed for the random number generator to determine the offset.

    Returns:
    str: The depersonalized data.

    Usage:
    >>> depersonalize("Hello123", seed=42)
    """
    def shift_letter(letter, letter_offset):
        if letter.isalpha():
            alphabet = string.ascii_uppercase if letter.isupper() else string.ascii_lowercase
            new_position = (alphabet.index(letter) + letter_offset) % 26
            return alphabet[new_position]
        return letter

    def offset_digit(digit, digit_offset):
        return str((int(digit) + digit_offset) % 10)

    if seed is not None:
        random.seed(seed)
        letter_offset = random.randint(1, 25)  # Offset between 1 and 25 for letters
        digit_offset = random.randint(1, 9)    # Offset between 1 and 9 for digits

    data_str = str(data)
    result = ''.join(shift_letter(char, letter_offset) if char.isalpha() else offset_digit(char, digit_offset) if char.isdigit() else char for char in data_str)
    return result

def repersonalize(data, seed=None):
    """
    Reverse the depersonalization process to retrieve the original data.

    Parameters:
    data (str): The depersonalized data to be repersonalized.
    seed (int, optional): The same seed used in the depersonalization process.

    Returns:
    str: The original data.

    Usage:
    >>> repersonalize("Ifmmp234", seed=42)
    """
    def shift_letter(letter, letter_offset):
        if letter.isalpha():
            alphabet = string.ascii_uppercase if letter.isupper() else string.ascii_lowercase
            new_position = (alphabet.index(letter) - letter_offset) % 26
            return alphabet[new_position]
        return letter

    def offset_digit(digit, digit_offset):
        return str((int(digit) - digit_offset) % 10)

    if seed is not None:
        random.seed(seed)
        letter_offset = random.randint(1, 25)  # Offset between 1 and 25 for letters
        digit_offset = random.randint(1, 9)    # Offset between 1 and 9 for digits

    data_str = str(data)
    result = ''.join(shift_letter(char, letter_offset) if char.isalpha() else offset_digit(char, digit_offset) if char.isdigit() else char for char in data_str)
    return result

# Example usage with a DataFrame
data = {'Person_ID': [12345, 67890]}
df = pd.DataFrame(data)




def shuffle_column_values(values, seed=None):
    unique_values = sorted(set(values))  # Sort the unique values
    shuffled_values = unique_values.copy()

    if seed is not None:
        random.seed(seed)

    random.shuffle(shuffled_values)

    value_to_index = {v: i for i, v in enumerate(unique_values)}
    shuffled_list = [shuffled_values[value_to_index[v]] for v in values]

    return shuffled_list




def unshuffle_column_values(shuffled_values, seed=None):
    unique_values = sorted(set(shuffled_values))  # Sort the unique values
    shuffled_order = unique_values.copy()

    if seed is not None:
        random.seed(seed)

    random.shuffle(shuffled_order)

    shuffled_to_original = {shuffled: original for shuffled, original in zip(shuffled_order, unique_values)}
    unshuffled_list = [shuffled_to_original[v] for v in shuffled_values]

    return unshuffled_list




# %% Example usage
seed = 42
ethnicities = ["Asian", "White", "Black", "Hispanic", "White", "Asian", "Black"]

shuffled_ethnicities = shuffle_column_values(ethnicities, seed=seed)
unshuffled_ethnicities = unshuffle_column_values(shuffled_ethnicities, seed=seed)

shuffled_ethnicities, unshuffled_ethnicities