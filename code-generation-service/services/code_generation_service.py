"""
Code Generation Service
Uses existing LLM services to generate code based on repository analysis and user requirements
"""
import os
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

from config.settings import Config
from services.code_analysis_service import CodeAnalysisService
from services.code_connector_service import CodeConnectorService
from utils.logger import setup_logger


class CodeGenerationService:
    """Service for generating code using existing LLM services"""
    
    def __init__(self):
        self.logger = setup_logger('code-generation')
        self.code_analysis = CodeAnalysisService()
        self.code_connector = CodeConnectorService()
    
    def generate_code(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate code based on user requirements and repository context
        
        Args:
            request: Code generation request containing:
                - repository_id: Connected repository identifier
                - requirements: User requirements/description
                - language: Target programming language
                - file_type: Type of code to generate (class, function, module, etc.)
                - context_files: Optional list of specific files to use as context
        
        Returns:
            Dictionary with generated code and metadata
        """
        try:
            repository_id = request.get('repository_id')
            requirements = request.get('requirements', '')
            target_language = request.get('language', 'python')
            file_type = request.get('file_type', 'function')
            context_files = request.get('context_files', [])
            
            if not repository_id:
                raise ValueError("Repository ID is required")
            
            if not requirements:
                raise ValueError("Requirements description is required")
            
            self.logger.info(f"Generating {file_type} in {target_language} for repository {repository_id}")
            
            # Get repository context
            repo_context = self._build_repository_context(repository_id, target_language, context_files)
            
            # Build code generation prompt
            prompt = self._build_code_generation_prompt(
                requirements, target_language, file_type, repo_context
            )
            
            # Generate code using LLM service
            self.logger.info(f"Calling LLM service with prompt length: {len(prompt)}")
            generated_code = self._call_llm_service(prompt, target_language)
            self.logger.info(f"LLM service returned code length: {len(generated_code) if generated_code else 0}")

            # Post-process and validate generated code
            processed_code = self._post_process_code(generated_code, target_language, file_type)

            return {
                "status": "success",
                "generated_code": processed_code,
                "language": target_language,
                "file_type": file_type,
                "repository_id": repository_id,
                "context_used": {
                    "repository_analysis": repo_context.get('summary', {}),
                    "language_info": repo_context.get('language_info', {}),
                    "code_style": repo_context.get('code_style', {}),
                    "example_files": len(repo_context.get('example_code', []))
                },
                "prompt_length": len(prompt),
                "raw_response_length": len(generated_code) if generated_code else 0,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Code generation failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_repository_context(self, repository_id: str, language: str, context_files: List[str]) -> Dict[str, Any]:
        """Build context from repository analysis"""
        try:
            # Get repository path
            repo_path = self.code_connector._get_repository_path(repository_id)
            if not repo_path:
                return {"error": "Repository not found"}
            
            # Analyze repository if not already done
            analysis = self.code_analysis.analyze_codebase(repo_path, language)
            
            # Build focused context
            context = {
                "language_info": analysis.get('languages', {}).get(language, {}),
                "code_style": analysis.get('languages', {}).get(language, {}).get('code_style', {}),
                "patterns": analysis.get('patterns', {}),
                "dependencies": analysis.get('dependencies', {}),
                "summary": analysis.get('summary', {}),
                "example_code": []
            }
            
            # Add specific file examples if requested
            if context_files:
                context['example_code'] = self._get_example_code(repo_path, context_files, language)
            else:
                # Get representative examples
                context['example_code'] = self._get_representative_examples(repo_path, language, analysis)
            
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to build repository context: {str(e)}")
            return {"error": str(e)}
    
    def _get_example_code(self, repo_path: str, file_paths: List[str], language: str) -> List[Dict[str, Any]]:
        """Get code examples from specific files"""
        examples = []
        
        for file_path in file_paths[:5]:  # Limit to 5 files
            try:
                full_path = os.path.join(repo_path, file_path)
                if os.path.exists(full_path) and Config.is_supported_file(file_path):
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Limit content size
                    if len(content) > 2000:
                        content = content[:2000] + "\n# ... (truncated)"
                    
                    examples.append({
                        "file": file_path,
                        "content": content,
                        "language": language
                    })
            except Exception as e:
                self.logger.warning(f"Failed to read example file {file_path}: {str(e)}")
                continue
        
        return examples
    
    def _get_representative_examples(self, repo_path: str, language: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get representative code examples from the repository"""
        examples = []
        
        try:
            # Get files for the target language
            # For now, we'll scan the directory directly
            files = []
            for root, dirs, filenames in os.walk(repo_path):
                dirs[:] = [d for d in dirs if not self._should_ignore(d)]
                for filename in filenames:
                    if Config.is_supported_file(filename):
                        file_path = os.path.join(root, filename)
                        rel_path = os.path.relpath(file_path, repo_path)
                        _, ext = os.path.splitext(filename)
                        file_language = Config.get_language_from_extension(ext)
                        if file_language == language:
                            files.append({"path": rel_path, "name": filename})
            
            # Select a few representative files
            selected_files = files[:3]  # Take first 3 files
            
            for file_info in selected_files:
                try:
                    full_path = os.path.join(repo_path, file_info['path'])
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Limit content size
                    if len(content) > 1500:
                        content = content[:1500] + "\n# ... (truncated)"
                    
                    examples.append({
                        "file": file_info['path'],
                        "content": content,
                        "language": language
                    })
                except Exception:
                    continue
        
        except Exception as e:
            self.logger.warning(f"Failed to get representative examples: {str(e)}")
        
        return examples
    
    def _build_code_generation_prompt(self, requirements: str, language: str, file_type: str, context: Dict[str, Any]) -> str:
        """Build a comprehensive prompt for code generation"""
        
        prompt_parts = [
            f"You are an expert {language} developer. Generate {file_type} code based on the following requirements and codebase context.",
            "",
            "## Requirements:",
            requirements,
            "",
            "## Target Language:",
            language,
            "",
            "## Code Type:",
            file_type,
            ""
        ]
        
        # Add repository context
        if context.get('language_info'):
            lang_info = context['language_info']
            prompt_parts.extend([
                "## Codebase Context:",
                f"- Total files: {lang_info.get('file_count', 0)}",
                f"- Total lines: {lang_info.get('total_lines', 0)}",
                ""
            ])
        
        # Add code style information
        if context.get('code_style'):
            style = context['code_style']
            prompt_parts.extend([
                "## Code Style Guidelines:",
                f"- Indentation: {style.get('indentation', 'unknown')}",
                f"- Average line length: {style.get('line_length', {}).get('avg', 0):.0f} characters",
                ""
            ])
        
        # Add dependencies context
        if context.get('dependencies'):
            deps = context['dependencies']
            prompt_parts.extend([
                "## Available Dependencies:",
                json.dumps(deps, indent=2),
                ""
            ])
        
        # Add example code
        if context.get('example_code'):
            prompt_parts.append("## Example Code from Repository:")
            for example in context['example_code'][:2]:  # Limit to 2 examples
                prompt_parts.extend([
                    f"### {example['file']}:",
                    "```" + example['language'],
                    example['content'],
                    "```",
                    ""
                ])
        
        prompt_parts.extend([
            "## Instructions:",
            f"1. Generate clean, well-documented {language} code that follows the existing codebase patterns",
            "2. Use the same code style and conventions as shown in the examples",
            "3. Include appropriate imports and dependencies",
            "4. Add comprehensive comments and docstrings",
            "5. Follow best practices for the target language",
            "6. Make the code production-ready and maintainable",
            "",
            "## Generated Code:"
        ])
        
        return "\n".join(prompt_parts)
    
    def _call_llm_service(self, prompt: str, language: str) -> str:
        """Call the existing LLM service to generate code"""
        try:
            # Try LLM prompt generation service first
            llm_url = Config.get_llm_prompt_service_url('llm/generate')
            
            payload = {
                "query": prompt,
                "use_rag": False,  # We're providing our own context
                "context": f"Generate {language} code based on the provided requirements and codebase context."
            }
            
            self.logger.info(f"Calling LLM service at: {llm_url}")
            
            response = requests.post(
                llm_url,
                json=payload,
                timeout=Config.LLM_REQUEST_TIMEOUT,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"LLM service response: {result}")

                # Handle the actual LLM service response format
                if result.get('status') == 'success':
                    # Try different response formats
                    response_text = (
                        result.get('response', '') or
                        result.get('data', {}).get('response', '') or
                        result.get('generated_text', '') or
                        str(result.get('data', ''))
                    )
                    return response_text
                else:
                    raise Exception(f"LLM service error: {result.get('error', 'Unknown error')}")
            else:
                # Fallback to main LLM service
                return self._call_fallback_llm_service(prompt, language)
                
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"LLM prompt service unavailable, trying fallback: {str(e)}")
            return self._call_fallback_llm_service(prompt, language)
        except Exception as e:
            self.logger.error(f"LLM service call failed: {str(e)}")
            raise e
    
    def _call_fallback_llm_service(self, prompt: str, language: str) -> str:
        """Fallback to main LLM service"""
        try:
            llm_url = Config.get_llm_service_url('llm/generate')
            
            payload = {
                "prompt": prompt,
                "max_tokens": Config.DEFAULT_MAX_TOKENS,
                "temperature": Config.DEFAULT_GENERATION_TEMPERATURE
            }
            
            response = requests.post(
                llm_url,
                json=payload,
                timeout=Config.LLM_REQUEST_TIMEOUT,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"Fallback LLM service response: {result}")

                if result.get('status') == 'success':
                    # Try different response formats for fallback service
                    response_text = (
                        result.get('data', {}).get('response', '') or
                        result.get('data', {}).get('generated_text', '') or
                        result.get('response', '') or
                        result.get('generated_text', '') or
                        str(result.get('data', ''))
                    )
                    return response_text
                else:
                    raise Exception(f"Fallback LLM service error: {result.get('error', 'Unknown error')}")
            else:
                raise Exception(f"Fallback LLM service returned status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.logger.error(f"Fallback LLM service call failed: {str(e)}")
            raise Exception(f"All LLM services unavailable: {str(e)}")
    
    def _post_process_code(self, generated_code: str, language: str, file_type: str) -> Dict[str, Any]:
        """Post-process and validate generated code"""
        try:
            # Extract code blocks if wrapped in markdown
            code_blocks = self._extract_code_blocks(generated_code, language)
            
            if code_blocks:
                main_code = code_blocks[0]['content']
            else:
                main_code = generated_code.strip()
            
            # Basic validation
            validation_result = self._validate_code(main_code, language)
            
            return {
                "code": main_code,
                "language": language,
                "file_type": file_type,
                "validation": validation_result,
                "raw_response": generated_code,
                "code_blocks": code_blocks
            }
            
        except Exception as e:
            self.logger.error(f"Code post-processing failed: {str(e)}")
            return {
                "code": generated_code,
                "language": language,
                "file_type": file_type,
                "validation": {"valid": False, "error": str(e)},
                "raw_response": generated_code
            }
    
    def _extract_code_blocks(self, text: str, language: str) -> List[Dict[str, Any]]:
        """Extract code blocks from markdown-formatted text"""
        import re
        
        # Pattern to match code blocks
        pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        code_blocks = []
        for lang, code in matches:
            code_blocks.append({
                "language": lang or language,
                "content": code.strip()
            })
        
        return code_blocks
    
    def _validate_code(self, code: str, language: str) -> Dict[str, Any]:
        """Basic code validation"""
        validation = {"valid": True, "errors": [], "warnings": []}
        
        try:
            if language == 'python':
                import ast
                ast.parse(code)
            # Add more language-specific validation as needed
            
        except SyntaxError as e:
            validation["valid"] = False
            validation["errors"].append(f"Syntax error: {str(e)}")
        except Exception as e:
            validation["warnings"].append(f"Validation warning: {str(e)}")
        
        return validation

    def _should_ignore(self, name: str) -> bool:
        """Check if file/directory should be ignored"""
        import fnmatch
        for pattern in Config.IGNORE_PATTERNS:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False
