# Installation Guide

## Quick Install

```bash
pip install fitviz-events
```

## Development Installation

1. Clone the repository:
```bash
git clone https://github.com/Fitness-Visualizer-Inc/fitviz-events.git
cd fitviz-events
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e .
```

4. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

## Verify Installation

```python
python -c "from fitviz_events import EventPublisher; print('Installation successful!')"
```

## Running Tests

```bash
pytest
```

## Building Distribution

```bash
python setup.py sdist bdist_wheel
```

## Publishing to PyPI

```bash
pip install twine
python setup.py sdist bdist_wheel
twine upload dist/*
```
