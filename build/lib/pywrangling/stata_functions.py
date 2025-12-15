import os

def create_color_styles(style_dir: str, color_dict: dict) -> None:
    """
    Creates Stata .style files for custom colors.

    Parameters:
    - style_dir (str): The directory where the .style files will be saved.
    - color_dict (dict): A dictionary where keys are color names and values are RGB codes as strings.
    
    Returns:
    None
    """
    if not os.path.exists(style_dir):
        raise ValueError(f"The directory {style_dir} does not exist.")
    
    for color_name, rgb_code in color_dict.items():
        # Create a valid file name by removing non-alphanumeric characters and converting to lowercase
        file_name = f"{style_dir}/color-{color_name.lower().replace('_', '')}.style"
        with open(file_name, "w") as file:
            file.write(f'set rgb "{rgb_code}"\n')

    print(f"Color .style files created successfully in {style_dir}")

