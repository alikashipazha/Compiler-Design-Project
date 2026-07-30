import re
from typing import Dict, List, Tuple

class LanguageDetector:
    """Heuristic statistical source code language classifier (C, Python, Java) (Section 7 - Bonus)."""
    
    C_KEYWORDS = ["struct", "void", "printf", "#include", "char*", "double", "#define", "int main"]
    PYTHON_KEYWORDS = ["def ", "import ", "elif ", "print(", "class ", "None", "True", "False", "pass", "self"]
    JAVA_KEYWORDS = ["public class", "static void", "System.out.println", "extends", "implements", "public static void main"]

    @staticmethod
    def detect(source_code: str) -> List[Tuple[str, float]]:
        """Analyzes the raw source code and returns a sorted list of (language, confidence_percentage) pairs."""
        source_code = source_code.strip()
        if not source_code:
            return [("C", 33.3), ("Python", 33.3), ("Java", 33.3)]

        # Initialize base scores slightly above zero to prevent mathematical anomalies
        scores: Dict[str, float] = {
            "C": 0.01,
            "Python": 0.01,
            "Java": 0.01
        }

        # 1. Shebang line check (High confidence for Python)
        lines = source_code.splitlines()
        first_line = lines[0].strip() if lines else ""
        if first_line.startswith("#!"):
            if "python" in first_line:
                scores["Python"] += 60.0
            elif "bash" in first_line or "sh" in first_line:
                scores["Python"] -= 20.0

        # 2. Delimiters and Punctuations (Semicolons & Curly Braces)
        semicolon_count = source_code.count(";")
        lbrace_count = source_code.count("{")
        rbrace_count = source_code.count("}")

        if lbrace_count > 0 or semicolon_count > 0:
            # Semicolons and curly braces are highly specific to C-like syntaxes
            scores["C"] += (lbrace_count * 5.0) + (semicolon_count * 3.0)
            scores["Java"] += (lbrace_count * 5.0) + (semicolon_count * 3.0)
            # Semicolons & braces heavily penalize Python's score
            scores["Python"] -= (lbrace_count * 8.0) + (semicolon_count * 5.0)

        # 3. Block colons (Python colons ending statements: e.g. def foo(): or if x:)
        # Matches colons followed by whitespace/newlines at the end of statements
        block_colons = len(re.findall(r":\s*(?:#.*)?$", source_code, re.MULTILINE))
        if block_colons > 0:
            scores["Python"] += block_colons * 10.0
            scores["C"] -= block_colons * 3.0
            scores["Java"] -= block_colons * 3.0

        # 4. Keyword Frequencies
        # C Keywords
        for kw in LanguageDetector.C_KEYWORDS:
            count = source_code.count(kw) if kw.startswith("#") else len(re.findall(r"\b" + re.escape(kw) + r"\b", source_code))
            scores["C"] += count * 6.0

        # Python Keywords
        for kw in LanguageDetector.PYTHON_KEYWORDS:
            count = len(re.findall(re.escape(kw), source_code))
            scores["Python"] += count * 6.0

        # Java Keywords
        for kw in LanguageDetector.JAVA_KEYWORDS:
            count = len(re.findall(re.escape(kw), source_code))
            scores["Java"] += count * 6.0
            # Matches to Java class features decrease C probability
            if count > 0:
                scores["C"] -= count * 2.0

        # 5. Normalize results to percentages (guaranteeing sum is 100.0)
        # Ensure no score remains negative
        for lang in scores:
            if scores[lang] < 0:
                scores[lang] = 0.0

        total_score = sum(scores.values())
        results: List[Tuple[str, float]] = []

        if total_score <= 0.05:
            # Equidistribute if no clear features are detected
            return [("C", 33.33), ("Python", 33.33), ("Java", 33.33)]

        for lang, score in scores.items():
            percentage = round((score / total_score) * 100, 1)
            results.append((lang, percentage))

        # Sort descending by confidence percentage
        return sorted(results, key=lambda x: x[1], reverse=True)