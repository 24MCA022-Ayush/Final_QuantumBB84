import json

def extract_values_to_separate_files(json_filepath, output_dir):
    """
    Extracts the "values" lists from each metric in a JSON file and
    stores them in separate TXT files within a specified output directory.

    Args:
        json_filepath: Path to the JSON file.
        output_dir: Path to the directory where output TXT files will be saved.
    """
    try:
        with open(json_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        import os
        if not os.path.exists(output_dir):  # Creates the output dir, if needed
           os.makedirs(output_dir)

        for metric_name, metric_data in data.items():
            output_filename = os.path.join(output_dir, f"{metric_name}_values.txt")
            with open(output_filename, 'w', encoding='utf-8') as outfile:
                for value in metric_data["values"]:
                    outfile.write(f"{value}\n")

        print(f"Values extracted and stored in separate files in '{output_dir}'")

    except FileNotFoundError:
        print(f"Error: File '{json_filepath}' not found.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{json_filepath}'.")
    except KeyError as e:                                # Handles if "values" is not present
        print(f"Error: 'values' key not found in metric {e}") # Gives more specific error message
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# Example usage (replace with your file paths and desired directory):
json_file = "qkd_stats.json"
output_directory = "Data"  # The directory where the files will be saved

extract_values_to_separate_files(json_file, output_directory)