import os
import sys

# Ensure python can locate src directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from cc_analyzer.presentation.highlighter import SyntaxHighlighter

def main():
    canonical_file_path = "tests/canonical_test.c"
    output_dir = "public"
    output_file_path = os.path.join(output_dir, "index.html")

    if not os.path.exists(canonical_file_path):
        print(f"Error: Canonical test file '{canonical_file_path}' not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Reading canonical test file: {canonical_file_path}...")
    with open(canonical_file_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    print("Running AST-guided Syntax Highlighter...")
    highlighter = SyntaxHighlighter(source_code)
    html_content = highlighter.highlight_html()

    print(f"Creating output directory: '{output_dir}'...")
    os.makedirs(output_dir, exist_ok=True)

    print(f"Writing highlighted index page: {output_file_path}...")
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print("Web report generated successfully!")

if __name__ == "__main__":
    main()