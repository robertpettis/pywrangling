
# %% Import Packages
import base64  # For encoding derived keys and encrypted output
import io  # In-memory buffers for dataframe serialization
import os  # For generating random salts
import random  # To generate random numbers
import re  # Regular expressions library for string manipulation
import string  # For alphabet string manipulation

import pandas as pd  # Dataframe handling
from cryptography.fernet import Fernet  # Authenticated symmetric encryption
from cryptography.hazmat.primitives import hashes  # Hash algorithms for key derivation
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC  # Password-based key derivation

# %% Functions



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




def _derive_key(key, salt):
    """
    Derive a Fernet-compatible key from a passphrase and salt using PBKDF2.

    Parameters:
    key (str): The passphrase to derive the key from.
    salt (bytes): Random salt (16 bytes).

    Returns:
    bytes: A url-safe base64-encoded 32-byte key for Fernet.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(key.encode("utf-8")))


def encrypt_df(df, key, path=None):
    """
    Encrypt a dataframe with a passphrase so only someone with the key can recover it.

    The dataframe is serialized to CSV in memory, then encrypted with Fernet
    (AES-128-CBC + HMAC) using a key derived from the passphrase via PBKDF2
    with a random salt. The salt is stored alongside the ciphertext, so the
    only thing you need to keep secret is the passphrase itself.

    Parameters:
    df (pd.DataFrame): The dataframe to encrypt.
    key (str): The passphrase. Anyone with this can decrypt, so keep it private.
    path (str, optional): If given, the encrypted bytes are also written to this file
        (e.g. 'data.enc'), which can then be committed to a public repo.

    Returns:
    bytes: The encrypted payload (salt + ciphertext).

    Usage:
    >>> token = encrypt_df(df, key="my secret passphrase", path="data.enc")
    """
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    salt = os.urandom(16)
    fernet = Fernet(_derive_key(key, salt))
    payload = salt + fernet.encrypt(buffer.getvalue().encode("utf-8"))

    if path is not None:
        with open(path, "wb") as f:
            f.write(payload)

    return payload


def decrypt_df(source, key):
    """
    Decrypt a dataframe previously encrypted with encrypt_df.

    Parameters:
    source (bytes or str): The encrypted payload returned by encrypt_df, or a
        path to a file it was written to.
    key (str): The same passphrase used to encrypt. A wrong passphrase raises
        an error rather than returning garbage data.

    Returns:
    pd.DataFrame: The original dataframe.

    Usage:
    >>> df = decrypt_df("data.enc", key="my secret passphrase")
    """
    if isinstance(source, str):
        with open(source, "rb") as f:
            source = f.read()

    salt, ciphertext = source[:16], source[16:]
    fernet = Fernet(_derive_key(key, salt))
    decrypted = fernet.decrypt(ciphertext).decode("utf-8")
    return pd.read_csv(io.StringIO(decrypted))


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