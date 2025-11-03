import os
import sys

def replace_words(directory, a, b):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    content = f.read()
                content = content.replace(a, b)
                with open(file_path, 'w') as f:
                    f.write(content)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Usage: python replace_words.py <directory> <a> <b>')
        sys.exit(1)
    replace_words(sys.argv[1], sys.argv[2], sys.argv[3])
