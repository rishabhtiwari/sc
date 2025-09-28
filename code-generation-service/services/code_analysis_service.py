"""
Code Analysis Service
Analyzes code repositories to extract patterns, styles, and context for code generation
"""
import os
import re
import ast
import json
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from collections import defaultdict, Counter

from config.settings import Config
from utils.logger import setup_logger


class CodeAnalysisService:
    """Service for analyzing code repositories and extracting patterns"""
    
    def __init__(self):
        self.logger = setup_logger('code-analysis')
    
    def analyze_codebase(self, repo_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a codebase to extract patterns, styles, and context
        
        Args:
            repo_path: Path to the repository
            language: Specific language to analyze (optional)
        
        Returns:
            Dictionary containing analysis results
        """
        try:
            self.logger.info(f"Analyzing codebase at: {repo_path}")
            
            analysis = {
                "repository_path": repo_path,
                "languages": {},
                "patterns": {},
                "dependencies": {},
                "code_style": {},
                "architecture": {},
                "summary": {}
            }
            
            # Get all code files
            code_files = self._get_code_files(repo_path, language)
            
            if not code_files:
                return {"error": "No code files found for analysis"}
            
            # Analyze each language separately
            languages_found = set()
            for file_info in code_files:
                languages_found.add(file_info['language'])
            
            for lang in languages_found:
                lang_files = [f for f in code_files if f['language'] == lang]
                analysis['languages'][lang] = self._analyze_language_files(lang_files, lang)
            
            # Extract cross-language patterns
            analysis['patterns'] = self._extract_patterns(code_files)
            
            # Analyze dependencies
            analysis['dependencies'] = self._analyze_dependencies(repo_path)
            
            # Generate summary
            analysis['summary'] = self._generate_analysis_summary(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze codebase: {str(e)}")
            return {"error": str(e)}
    
    def _get_code_files(self, repo_path: str, language: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all code files from repository"""
        code_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not self._should_ignore(d)]
            
            for file in files:
                if self._should_ignore(file):
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)
                
                # Check file size
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > Config.MAX_FILE_SIZE_KB * 1024:
                        continue
                except OSError:
                    continue
                
                # Determine language
                _, ext = os.path.splitext(file)
                file_language = Config.get_language_from_extension(ext)
                
                if file_language != 'unknown':
                    if language is None or file_language == language:
                        code_files.append({
                            "path": file_path,
                            "relative_path": rel_path,
                            "name": file,
                            "language": file_language,
                            "size": file_size
                        })
        
        return code_files
    
    def _analyze_language_files(self, files: List[Dict[str, Any]], language: str) -> Dict[str, Any]:
        """Analyze files for a specific programming language"""
        analysis = {
            "file_count": len(files),
            "total_lines": 0,
            "functions": [],
            "classes": [],
            "imports": [],
            "code_style": {},
            "patterns": []
        }
        
        for file_info in files:
            try:
                with open(file_info['path'], 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Count lines
                lines = content.split('\n')
                analysis['total_lines'] += len(lines)
                
                # Language-specific analysis
                if language == 'python':
                    file_analysis = self._analyze_python_file(content, file_info['relative_path'])
                elif language == 'java':
                    file_analysis = self._analyze_java_file(content, file_info['relative_path'])
                elif language in ['javascript', 'typescript']:
                    file_analysis = self._analyze_js_file(content, file_info['relative_path'])
                else:
                    file_analysis = self._analyze_generic_file(content, file_info['relative_path'])
                
                # Merge file analysis into language analysis
                if 'functions' in file_analysis:
                    analysis['functions'].extend(file_analysis['functions'])
                if 'classes' in file_analysis:
                    analysis['classes'].extend(file_analysis['classes'])
                if 'imports' in file_analysis:
                    analysis['imports'].extend(file_analysis['imports'])
                
            except Exception as e:
                self.logger.warning(f"Failed to analyze file {file_info['path']}: {str(e)}")
                continue
        
        # Analyze code style patterns
        analysis['code_style'] = self._analyze_code_style(files, language)
        
        return analysis
    
    def _analyze_python_file(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze Python file using AST"""
        analysis = {
            "functions": [],
            "classes": [],
            "imports": []
        }
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis['functions'].append({
                        "name": node.name,
                        "file": file_path,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "decorators": [ast.unparse(d) for d in node.decorator_list] if hasattr(ast, 'unparse') else []
                    })
                
                elif isinstance(node, ast.ClassDef):
                    analysis['classes'].append({
                        "name": node.name,
                        "file": file_path,
                        "line": node.lineno,
                        "bases": [ast.unparse(base) for base in node.bases] if hasattr(ast, 'unparse') else [],
                        "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    })
                
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            analysis['imports'].append({
                                "module": alias.name,
                                "alias": alias.asname,
                                "type": "import",
                                "file": file_path
                            })
                    else:  # ImportFrom
                        module = node.module or ""
                        for alias in node.names:
                            analysis['imports'].append({
                                "module": f"{module}.{alias.name}" if module else alias.name,
                                "alias": alias.asname,
                                "type": "from_import",
                                "file": file_path
                            })
        
        except SyntaxError as e:
            self.logger.warning(f"Syntax error in Python file {file_path}: {str(e)}")
        
        return analysis
    
    def _analyze_java_file(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze Java file using regex patterns"""
        analysis = {
            "functions": [],
            "classes": [],
            "imports": []
        }
        
        # Extract imports
        import_pattern = r'import\s+(static\s+)?([a-zA-Z_][a-zA-Z0-9_.]*(?:\.\*)?);'
        for match in re.finditer(import_pattern, content):
            analysis['imports'].append({
                "module": match.group(2),
                "static": bool(match.group(1)),
                "file": file_path
            })
        
        # Extract classes
        class_pattern = r'(?:public\s+|private\s+|protected\s+)?(?:abstract\s+|final\s+)?class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        for match in re.finditer(class_pattern, content):
            analysis['classes'].append({
                "name": match.group(1),
                "file": file_path
            })
        
        # Extract methods
        method_pattern = r'(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:final\s+)?[a-zA-Z_][a-zA-Z0-9_<>\[\]]*\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)'
        for match in re.finditer(method_pattern, content):
            analysis['functions'].append({
                "name": match.group(1),
                "file": file_path
            })
        
        return analysis
    
    def _analyze_js_file(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript file using regex patterns"""
        analysis = {
            "functions": [],
            "classes": [],
            "imports": []
        }
        
        # Extract imports (ES6 modules)
        import_patterns = [
            r'import\s+(?:\{[^}]+\}|\*\s+as\s+\w+|\w+)\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'import\s+[\'"]([^\'"]+)[\'"]',
            r'const\s+\w+\s+=\s+require\([\'"]([^\'"]+)[\'"]\)'
        ]
        
        for pattern in import_patterns:
            for match in re.finditer(pattern, content):
                analysis['imports'].append({
                    "module": match.group(1),
                    "file": file_path
                })
        
        # Extract functions
        function_patterns = [
            r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            r'const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>',
            r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(?:async\s+)?function\s*\('
        ]
        
        for pattern in function_patterns:
            for match in re.finditer(pattern, content):
                analysis['functions'].append({
                    "name": match.group(1),
                    "file": file_path
                })
        
        # Extract classes
        class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        for match in re.finditer(class_pattern, content):
            analysis['classes'].append({
                "name": match.group(1),
                "file": file_path
            })
        
        return analysis
    
    def _analyze_generic_file(self, content: str, file_path: str) -> Dict[str, Any]:
        """Generic analysis for unsupported languages"""
        return {
            "functions": [],
            "classes": [],
            "imports": []
        }
    
    def _analyze_code_style(self, files: List[Dict[str, Any]], language: str) -> Dict[str, Any]:
        """Analyze code style patterns"""
        style_analysis = {
            "indentation": "unknown",
            "line_length": {"avg": 0, "max": 0},
            "naming_convention": {},
            "comment_style": []
        }
        
        total_lines = 0
        total_length = 0
        indentation_counts = Counter()
        
        for file_info in files[:10]:  # Analyze first 10 files for performance
            try:
                with open(file_info['path'], 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for line in lines:
                    total_lines += 1
                    line_length = len(line.rstrip())
                    total_length += line_length
                    style_analysis['line_length']['max'] = max(style_analysis['line_length']['max'], line_length)
                    
                    # Analyze indentation
                    if line.strip():  # Non-empty line
                        leading_spaces = len(line) - len(line.lstrip(' '))
                        leading_tabs = len(line) - len(line.lstrip('\t'))
                        
                        if leading_spaces > 0:
                            indentation_counts['spaces'] += 1
                        elif leading_tabs > 0:
                            indentation_counts['tabs'] += 1
            
            except Exception:
                continue
        
        # Determine indentation style
        if indentation_counts:
            style_analysis['indentation'] = indentation_counts.most_common(1)[0][0]
        
        # Calculate average line length
        if total_lines > 0:
            style_analysis['line_length']['avg'] = total_length / total_lines
        
        return style_analysis
    
    def _extract_patterns(self, code_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract common patterns across the codebase"""
        patterns = {
            "common_imports": Counter(),
            "file_structure": {},
            "naming_patterns": []
        }
        
        # Analyze file structure patterns
        directories = set()
        for file_info in code_files:
            dir_path = os.path.dirname(file_info['relative_path'])
            if dir_path:
                directories.add(dir_path)
        
        patterns['file_structure']['directories'] = list(directories)
        
        return patterns
    
    def _analyze_dependencies(self, repo_path: str) -> Dict[str, Any]:
        """Analyze project dependencies"""
        dependencies = {}
        
        # Check for common dependency files
        dependency_files = {
            'package.json': 'npm',
            'requirements.txt': 'pip',
            'pom.xml': 'maven',
            'build.gradle': 'gradle',
            'Cargo.toml': 'cargo',
            'go.mod': 'go',
            'composer.json': 'composer'
        }
        
        for dep_file, package_manager in dependency_files.items():
            file_path = os.path.join(repo_path, dep_file)
            if os.path.exists(file_path):
                dependencies[package_manager] = self._parse_dependency_file(file_path, package_manager)
        
        return dependencies
    
    def _parse_dependency_file(self, file_path: str, package_manager: str) -> Dict[str, Any]:
        """Parse dependency file based on package manager"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if package_manager == 'npm':
                data = json.loads(content)
                return {
                    "dependencies": data.get('dependencies', {}),
                    "devDependencies": data.get('devDependencies', {})
                }
            elif package_manager == 'pip':
                deps = []
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        deps.append(line)
                return {"dependencies": deps}
            
            # Add more parsers as needed
            return {"raw_content": content[:500]}  # First 500 chars
            
        except Exception as e:
            self.logger.warning(f"Failed to parse {file_path}: {str(e)}")
            return {"error": str(e)}
    
    def _generate_analysis_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the analysis"""
        summary = {
            "total_languages": len(analysis['languages']),
            "primary_language": None,
            "total_files": 0,
            "total_lines": 0,
            "architecture_type": "unknown"
        }
        
        # Find primary language
        max_lines = 0
        for lang, lang_data in analysis['languages'].items():
            total_lines = lang_data.get('total_lines', 0)
            summary['total_lines'] += total_lines
            summary['total_files'] += lang_data.get('file_count', 0)
            
            if total_lines > max_lines:
                max_lines = total_lines
                summary['primary_language'] = lang
        
        return summary
    
    def _should_ignore(self, name: str) -> bool:
        """Check if file/directory should be ignored"""
        import fnmatch
        for pattern in Config.IGNORE_PATTERNS:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False
