from pathlib import Path
print(next(line.split('=', 1)[1].strip() for line in (Path(__file__).resolve().parents[1] / 'gradle.properties').read_text().splitlines() if line.startswith('version')))
