# Book Manager API Documentation

## Core Components

### Text Analysis

```python
from book_manager.analysis.text_analysis import TextAnalyzer, analyze_scene

# Create analyzer instance
analyzer = TextAnalyzer()

# Analyze a scene
results = analyze_scene(Path("scene.md"))
```

Key Classes and Methods:

#### TextAnalyzer
- `analyze_scene(file_path: Path, use_cache: bool = True) -> Optional[Dict]`
  - Analyzes a scene file for word count, term frequency, and TODOs
  - Returns dictionary with analysis results
  
- `get_word_frequency(text: str, stopwords: Set[str]) -> Counter`
  - Calculates word frequency excluding stopwords
  
- `extract_todos(text: str) -> List[str]`
  - Extracts TODO items from text

### Compilation

```python
from book_manager.compile.compiler import compile_manuscript

# Compile manuscript
success, files = compile_manuscript(structure, formats=['pdf', 'docx'])
```

Key Classes:

#### CompilationConfig
- Handles format-specific configuration
- Manages pandoc arguments
- Validates output formats

#### ManuscriptCompiler
- Manages the compilation process
- Handles temporary files
- Provides progress tracking

### Configuration Management

```python
from book_manager.utils.config_loader import load_config, get_config

# Load configuration
load_config("config.yaml")
config = get_config()
```

## Type Definitions

```python
Structure = Dict[int, Dict[int, List[Dict[str, Any]]]]
# Example:
# {
#     1: {  # Book number
#         1: [  # Act number
#             {
#                 'path': Path,
#                 'scene_num': int,
#                 'word_count': int,
#                 'top_words': List[str],
#                 'todos': List[str]
#             }
#         ]
#     }
# }
```

## Error Handling

Custom exceptions:
- `BookManagerError`: Base exception class
- `CompilationError`: Compilation-specific errors
- `PandocMissingError`: When pandoc is not available

## Performance Considerations

- Use caching when possible
- Large files (>10MB) are rejected by default
- Memory usage is managed via LRU cache


