import os

def search_for_debug_true(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and not file == 'manual_testing.py':
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        contents = f.read()
                        if 'DEBUG = True' in contents:
                            print(f"Found 'DEBUG = True' in: {file_path}")
                            return False
                except (IOError, UnicodeDecodeError) as e:
                    print(f"Error reading {file_path}: {e}")
    
    print("No 'DEBUG = True' found.")
    return True

if __name__ == "__main__":
    directory_to_search = '..'
    result = search_for_debug_true(directory_to_search)
    print("Result:", result)
