
# %% Import Packages
import base64  # For encoding derived keys and encrypted output
import hashlib  # For deriving deterministic seeds from passphrases
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


def _letter_table(key, inverse=False):
    """
    Build a letter-substitution table from a passphrase.

    The passphrase is hashed to seed a shuffle of the alphabet, so the same
    key always produces the same mapping (e.g. every 'd' becomes 'w').
    Case is preserved; digits, punctuation, and whitespace are untouched.

    Parameters:
    key (str): The passphrase the mapping is derived from.
    inverse (bool): If True, return the reverse mapping to undo the scramble.

    Returns:
    dict: A translation table for str.translate.
    """
    seed = int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")
    letters = list(string.ascii_lowercase)
    shuffled = letters.copy()
    random.Random(seed).shuffle(shuffled)

    if inverse:
        letters, shuffled = shuffled, letters

    mapping = {}
    for original, replacement in zip(letters, shuffled):
        mapping[original] = replacement
        mapping[original.upper()] = replacement.upper()
    return str.maketrans(mapping)


def _oneway_letter_table():
    """
    Build a random, many-to-one letter mapping that cannot be undone.

    Each of the 26 letters is independently assigned a random replacement
    drawn with replacement, so several letters collapse onto the same output
    (e.g. both 'd' and 'k' might become 'w'). The mapping is generated from
    os.urandom and never stored, so the original letters are unrecoverable
    even by whoever ran the scramble.

    Returns:
    dict: A translation table for str.translate.
    """
    rng = random.Random(int.from_bytes(os.urandom(16), "big"))
    letters = list(string.ascii_lowercase)
    replacements = rng.choices(letters, k=26)

    mapping = {}
    for original, replacement in zip(letters, replacements):
        mapping[original] = replacement
        mapping[original.upper()] = replacement.upper()
    return str.maketrans(mapping)


def scramble_letters(df, key=None, irreversible=False):
    """
    Make a pseudo-synthetic copy of a dataframe by substituting letters.

    Every letter in every string cell is swapped via a substitution mapping
    (e.g. all 'd's become 'w's), so values keep their shape and look plausible
    but are no longer the real data. Numbers, dates, and non-string columns
    are left unchanged.

    By default the mapping is derived from the key, so the scramble is
    reversible with unscramble_letters and the same key. With
    irreversible=True the mapping is instead generated randomly, never
    stored, and deliberately collapses several letters onto the same output,
    so the original values cannot be recovered by anyone — including you.

    Note the reversible mode is obfuscation, not encryption — letter
    frequencies are preserved, so treat it as a way to make data
    look-but-not-be real, not as protection for genuinely sensitive values.
    Even the irreversible mode preserves word lengths and leaves numbers and
    dates intact, so it is not a substitute for real anonymization of
    sensitive data.

    Parameters:
    df (pd.DataFrame): The dataframe to scramble.
    key (str, optional): The passphrase the letter mapping is derived from.
        Required unless irreversible=True, where it is ignored.
    irreversible (bool, optional): If True, use a random throwaway
        many-to-one mapping that can never be undone.

    Returns:
    pd.DataFrame: A scrambled copy of the dataframe.

    Usage:
    >>> fake_df = scramble_letters(df, key="my secret passphrase")
    >>> fake_df = scramble_letters(df, irreversible=True)
    """
    if irreversible:
        table = _oneway_letter_table()
    elif key is None:
        raise ValueError("A key is required unless irreversible=True.")
    else:
        table = _letter_table(key)

    return df.apply(lambda col: col.map(lambda v: v.translate(table) if isinstance(v, str) else v))


def unscramble_letters(df, key):
    """
    Reverse scramble_letters, recovering the original dataframe values.

    Only works for key-based scrambles; data scrambled with
    irreversible=True cannot be recovered by design.

    Parameters:
    df (pd.DataFrame): A dataframe scrambled with scramble_letters.
    key (str): The same passphrase used to scramble.

    Returns:
    pd.DataFrame: The dataframe with original letters restored.

    Usage:
    >>> df = unscramble_letters(fake_df, key="my secret passphrase")
    """
    table = _letter_table(key, inverse=True)
    return df.apply(lambda col: col.map(lambda v: v.translate(table) if isinstance(v, str) else v))


def encrypt_df(df, key, path=None, scramble=False):
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
    scramble (bool, optional): If True, letters in string cells are first swapped
        via a key-derived substitution (see scramble_letters), so even the
        decrypted data is pseudo-synthetic. Pass scramble=True to decrypt_df
        to fully recover the original values.

    Returns:
    bytes: The encrypted payload (salt + ciphertext).

    Usage:
    >>> token = encrypt_df(df, key="my secret passphrase", path="data.enc")
    """
    if scramble:
        df = scramble_letters(df, key)

    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    salt = os.urandom(16)
    fernet = Fernet(_derive_key(key, salt))
    payload = salt + fernet.encrypt(buffer.getvalue().encode("utf-8"))

    if path is not None:
        with open(path, "wb") as f:
            f.write(payload)

    return payload


def decrypt_df(source, key, scramble=False):
    """
    Decrypt a dataframe previously encrypted with encrypt_df.

    Parameters:
    source (bytes or str): The encrypted payload returned by encrypt_df, or a
        path to a file it was written to.
    key (str): The same passphrase used to encrypt. A wrong passphrase raises
        an error rather than returning garbage data.
    scramble (bool, optional): If the data was encrypted with scramble=True,
        pass True here as well to reverse the letter substitution.

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
    df = pd.read_csv(io.StringIO(decrypted))

    if scramble:
        df = unscramble_letters(df, key)

    return df


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