
# %% Import Packages
import random  # To generate random numbers
import re  # Regular expressions library for string manipulation
import string  # For alphabet string manipulation

# %% Functions

def depersonalize_numbers(data, seed=None):
    """
    Depersonalize data by adding a random offset to each digit, based on the seed.

    Parameters:
    data (int, float, str): The data to be depersonalized. Can be a number or a string.
    seed (int, optional): A seed for the random number generator to determine the offset.

    Returns:
    int, float, str: The depersonalized data.

    Usage:
    >>> depersonalize_numbers(11234323, seed=42)
    >>> depersonalize_numbers("124rf234", seed=42)
    """
    def offset_digit(digit, offset):
        return str((int(digit) + offset) % 10)

    if seed is not None:
        random.seed(seed)
        offset = random.randint(1, 9)  # Offset between 1 and 9

    if isinstance(data, (int, float)):
        return int("".join(offset_digit(d, offset) for d in str(data)))
    elif isinstance(data, str):
        return re.sub(r'\d', lambda x: offset_digit(x.group(), offset), data)

    return data

def repersonalize_numbers(data, seed=None):
    """
    Reverse the depersonalization process to retrieve the original data.

    Parameters:
    data (int, float, str): The depersonalized data to be repersonalized.
    seed (int, optional): The same seed used in the depersonalization process.

    Returns:
    int, float, str: The original data.

    Usage:
    >>> repersonalize_numbers(95822412, seed=42)
    >>> repersonalize_numbers("104rf332", seed=42)
    """
    def offset_digit(digit, offset):
        return str((int(digit) - offset) % 10)

    if seed is not None:
        random.seed(seed)
        offset = random.randint(1, 9)  # Offset between 1 and 9

    if isinstance(data, (int, float)):
        return int("".join(offset_digit(d, offset) for d in str(data)))
    elif isinstance(data, str):
        return re.sub(r'\d', lambda x: offset_digit(x.group(), offset), data)

    return data

def depersonalize_letters(data, seed=None):
    """
    Depersonalize letters in the given string by shifting them a random offset based on the seed.

    Parameters:
    data (str): The string to be depersonalized.
    seed (int, optional): A seed for the random number generator to determine the offset.

    Returns:
    str: The depersonalized string.

    Usage:
    >>> depersonalize_letters("Hello World", seed=42)
    """
    def shift_letter(letter, offset):
        if letter.isalpha():
            alphabet = string.ascii_uppercase if letter.isupper() else string.ascii_lowercase
            new_position = (alphabet.index(letter) + offset) % 26
            return alphabet[new_position]
        return letter

    if seed is not None:
        random.seed(seed)
        offset = random.randint(1, 25)  # Offset between 1 and 25

    return ''.join(shift_letter(l, offset) for l in data)

def repersonalize_letters(data, seed=None):
    """
    Reverse the depersonalization process to retrieve the original string.

    Parameters:
    data (str): The depersonalized string to be repersonalized.
    seed (int, optional): The same seed used in the depersonalization process.

    Returns:
    str: The original string.

    Usage:
    >>> repersonalize_letters("Ifmmp Xpsme", seed=42)
    """
    def shift_letter(letter, offset):
        if letter.isalpha():
            alphabet = string.ascii_uppercase if letter.isupper() else string.ascii_lowercase
            new_position = (alphabet.index(letter) - offset) % 26
            return alphabet[new_position]
        return letter

    if seed is not None:
        random.seed(seed)
        offset = random.randint(1, 25)  # Offset between 1 and 25

    return ''.join(shift_letter(l, offset) for l in data)


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