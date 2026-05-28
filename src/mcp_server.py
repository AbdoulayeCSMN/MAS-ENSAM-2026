"""MCP (Model Context Protocol) Server - Independent from REST API."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph.workflow import build_workflow
from graph.state import AgentState
from memory.persistent import PersistentMemory
from llm.client import LLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPServer:
    """
    Model Context Protocol Server
    Implements the MCP standard for tool calling and context exchange.
    """
    
    def __init__(self):
        self.workflow = build_workflow()
        self.memory = PersistentMemory()
        self.llm = LLMClient()
        self.tools_registry = {}
        self._register_tools()
        
    def _register_tools(self):
        """Register all available MCP tools."""
        self.tools_registry = {
            "scan_repository": {
                "handler": self._scan_repository,
                "description": "Scan a repository for security vulnerabilities",
                "parameters": {
                    "repo_path": {"type": "string", "required": True},
                    "languages": {"type": "array", "required": False},
                    "max_iterations": {"type": "integer", "required": False, "default": 3}
                }
            },
            "analyze_code": {
                "handler": self._analyze_code,
                "description": "Analyze a code snippet for vulnerabilities",
                "parameters": {
                    "code": {"type": "string", "required": True},
                    "language": {"type": "string", "required": True},
                    "context": {"type": "object", "required": False}
                }
            },
            "generate_patch": {
                "handler": self._generate_patch,
                "description": "Generate a security patch for a vulnerability",
                "parameters": {
                    "vulnerability_id": {"type": "string", "required": True},
                    "file_path": {"type": "string", "required": True},
                    "code_snippet": {"type": "string", "required": True},
                    "description": {"type": "string", "required": False}
                }
            },
            "enrich_finding": {
                "handler": self._enrich_finding,
                "description": "Add AI context and remediation to a finding",
                "parameters": {
                    "finding": {"type": "object", "required": True},
                    "detail_level": {"type": "string", "required": False, "default": "normal"}
                }
            },
            "query_memory": {
                "handler": self._query_memory,
                "description": "Query persistent memory for similar patterns",
                "parameters": {
                    "query": {"type": "string", "required": True},
                    "top_k": {"type": "integer", "required": False, "default": 5},
                    "memory_type": {"type": "string", "required": False, "default": "patterns"}
                }
            },
            "store_pattern": {
                "handler": self._store_pattern,
                "description": "Store a vulnerability pattern in persistent memory",
                "parameters": {
                    "pattern": {"type": "string", "required": True},
                    "code_snippet": {"type": "string", "required": True},
                    "cwe_id": {"type": "string", "required": False}
                }
            },
            "get_agent_status": {
                "handler": self._get_agent_status,
                "description": "Get status of all agents",
                "parameters": {}
            },
            "get_agent_capabilities": {
                "handler": self._get_agent_capabilities,
                "description": "Get detailed capabilities of a specific agent",
                "parameters": {
                    "agent_name": {"type": "string", "required": True}
                }
            },
            "explain_vulnerability": {
                "handler": self._explain_vulnerability,
                "description": "Get detailed explanation of a vulnerability",
                "parameters": {
                    "cwe_id": {"type": "string", "required": True},
                    "context": {"type": "string", "required": False}
                }
            }
        }
    
    # ============================================
    # MCP PROTOCOL METHODS
    # ============================================
    
    def get_protocol_info(self) -> dict:
        """Return MCP protocol information."""
        return {
            "protocol": "Model Context Protocol",
            "version": "2024-11-05",
            "name": "Multi-Agent Security Scanner MCP Server",
            "description": "MCP server for security scanning with multi-agent orchestration",
            "tools_count": len(self.tools_registry)
        }
    
    def list_tools(self) -> list[dict]:
        """List all available tools (MCP standard)."""
        tools = []
        for name, tool in self.tools_registry.items():
            tools.append({
                "name": name,
                "description": tool["description"],
                "parameters": tool["parameters"],
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        param: {
                            "type": info["type"],
                            "description": f"Parameter: {param}"
                        }
                        for param, info in tool["parameters"].items()
                    },
                    "required": [
                        param for param, info in tool["parameters"].items()
                        if info.get("required", False)
                    ]
                }
            })
        return tools
    
    def call_tool(self, tool_name: str, arguments: dict, context: dict = None) -> dict:
        """
        Call a tool (MCP standard).
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            context: Optional context (scan_id, session, etc.)
        
        Returns:
            Tool execution result
        """
        logger.info(f"MCP call: {tool_name} with args: {arguments}")
        
        if tool_name not in self.tools_registry:
            return {
                "error": {
                    "code": -32601,
                    "message": f"Tool not found: {tool_name}",
                    "data": {"available_tools": list(self.tools_registry.keys())}
                }
            }
        
        try:
            handler = self.tools_registry[tool_name]["handler"]
            result = handler(arguments, context)
            return {
                "result": result,
                "tool": tool_name,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"MCP tool error: {e}")
            return {
                "error": {
                    "code": -32000,
                    "message": str(e),
                    "tool": tool_name
                },
                "status": "error"
            }
    
    # ============================================
    # TOOL HANDLERS
    # ============================================
    
    async def _scan_repository(self, args: dict, context: dict = None) -> dict:
        """Handle scan_repository tool."""
        repo_path = args.get("repo_path")
        if not repo_path:
            raise ValueError("repo_path is required")
        
        max_iterations = args.get("max_iterations", 3)
        scan_id = str(uuid.uuid4())[:8]
        
        state = AgentState(
            repo_root=repo_path,
            scan_id=scan_id,
            max_patch_iterations=max_iterations
        )
        
        # Execute workflow
        final_state = await self.workflow.ainvoke(state)
        
        return {
            "scan_id": scan_id,
            "repo_path": repo_path,
            "findings_count": len(final_state.vulnerabilities),
            "exploitable_count": sum(1 for v in final_state.vulnerabilities if v.is_exploitable),
            "patches_generated": len(final_state.patches_validated),
            "summary": {
                "critical": sum(1 for v in final_state.vulnerabilities if v.severity.value == "critical"),
                "high": sum(1 for v in final_state.vulnerabilities if v.severity.value == "high"),
                "medium": sum(1 for v in final_state.vulnerabilities if v.severity.value == "medium"),
                "low": sum(1 for v in final_state.vulnerabilities if v.severity.value == "low")
            }
        }
    
    def _analyze_code(self, args: dict, context: dict = None) -> dict:
        """Handle analyze_code tool."""
        code = args.get("code")
        language = args.get("language", "python")
        
        if not code:
            raise ValueError("code is required")
        
        prompt = f"""Analyze this {language} code for security vulnerabilities.
        Return JSON with: severity, type, line, description, fix.
        
        Code:
        ```{language}
        {code[:2000]}
        ```"""
        
        analysis = self.llm.query(
            system="You are a security expert. Analyze code and return JSON.",
            user=prompt,
            model="fast"
        )
        
        return {
            "language": language,
            "code_length": len(code),
            "analysis": analysis,
            "timestamp": self._get_timestamp()
        }
    
    def _generate_patch(self, args: dict, context: dict = None) -> dict:
        """Handle generate_patch tool."""
        vuln_id = args.get("vulnerability_id")
        file_path = args.get("file_path")
        code_snippet = args.get("code_snippet")
        description = args.get("description", "")
        
        if not vuln_id or not file_path or not code_snippet:
            raise ValueError("vulnerability_id, file_path, and code_snippet are required")
        
        prompt = f"""Generate a security patch for this vulnerability.
        
        Vulnerability ID: {vuln_id}
        Description: {description}
        
        Vulnerable code:
        ```{code_snippet}```
        
        Generate a unified diff format patch."""
        
        patch = self.llm.query(
            system="You are a security engineer. Generate minimal, correct patches in unified diff format.",
            user=prompt,
            model="strong"
        )
        
        return {
            "vulnerability_id": vuln_id,
            "file_path": file_path,
            "patch": patch,
            "patch_format": "unified_diff",
            "generated_at": self._get_timestamp()
        }
    
    def _enrich_finding(self, args: dict, context: dict = None) -> dict:
        """Handle enrich_finding tool."""
        finding = args.get("finding", {})
        detail_level = args.get("detail_level", "normal")
        
        if not finding:
            raise ValueError("finding is required")
        
        prompt = f"""Enrich this security finding with:
        - Severity (Critical/High/Medium/Low)
        - Likelihood (High/Medium/Low)
        - Impact description
        - Remediation steps
        - References (CWE, OWASP)
        
        Finding: {json.dumps(finding, indent=2)}
        
        Provide enrichment as JSON."""
        
        enrichment = self.llm.query(
            system="You are a security expert. Provide structured enrichment data.",
            user=prompt,
            model="fast"
        )
        
        return {
            "original_finding": finding,
            "enrichment": json.loads(enrichment) if self._is_json(enrichment) else {"raw": enrichment},
            "detail_level": detail_level,
            "enriched_at": self._get_timestamp()
        }
    
    def _query_memory(self, args: dict, context: dict = None) -> dict:
        """Handle query_memory tool."""
        query = args.get("query")
        top_k = args.get("top_k", 5)
        memory_type = args.get("memory_type", "patterns")
        
        if not query:
            raise ValueError("query is required")
        
        if not self.memory._enabled:
            return {
                "memory_available": False,
                "message": "Persistent memory not available. Install qdrant-client and sentence-transformers"
            }
        
        if memory_type == "patterns":
            results = self.memory.retrieve_similar_patterns([query], top_k)
        else:
            results = self.memory.retrieve_patches(query, top_k)
        
        return {
            "query": query,
            "memory_type": memory_type,
            "results_count": len(results),
            "results": results,
            "memory_backend": "Qdrant"
        }
    
    def _store_pattern(self, args: dict, context: dict = None) -> dict:
        """Handle store_pattern tool."""
        pattern = args.get("pattern")
        code_snippet = args.get("code_snippet")
        cwe_id = args.get("cwe_id")
        
        if not pattern or not code_snippet:
            raise ValueError("pattern and code_snippet are required")
        
        if not self.memory._enabled:
            return {
                "stored": False,
                "message": "Persistent memory not available"
            }
        
        self.memory.store_pattern(pattern, code_snippet)
        
        return {
            "stored": True,
            "pattern": pattern[:100],
            "cwe_id": cwe_id,
            "stored_at": self._get_timestamp()
        }
    
    def _get_agent_status(self, args: dict, context: dict = None) -> dict:
        """Handle get_agent_status tool."""
        agents = [
            {"name": "triage", "status": "active", "type": "orchestrator"},
            {"name": "scanner", "status": "active", "type": "static_analysis"},
            {"name": "memory_safety", "status": "active", "type": "dynamic_analysis"},
            {"name": "semantic_analyst", "status": "active", "type": "llm_based"},
            {"name": "exploit_scorer", "status": "active", "type": "risk_assessment"},
            {"name": "enricher", "status": "active", "type": "ai_enhancement"},
            {"name": "patcher", "status": "active", "type": "remediation"},
            {"name": "validator", "status": "active", "type": "verification"},
            {"name": "report", "status": "active", "type": "output"}
        ]
        
        return {
            "total_agents": len(agents),
            "active_agents": sum(1 for a in agents if a["status"] == "active"),
            "agents": agents,
            "workflow_status": "ready"
        }
    
    def _get_agent_capabilities(self, args: dict, context: dict = None) -> dict:
        """Handle get_agent_capabilities tool."""
        agent_name = args.get("agent_name")
        
        if not agent_name:
            raise ValueError("agent_name is required")
        
        capabilities = {
            "triage": {
                "description": "Language detection and routing",
                "methods": ["detect_languages", "classify_targets", "extract_files"],
                "input": "repository path",
                "output": "list of targets with languages"
            },
            "scanner": {
                "description": "Static code analysis",
                "methods": ["semgrep_scan", "bandit_scan", "gosec_scan", "parallel_execution"],
                "input": "target files with languages",
                "output": "raw vulnerability findings"
            },
            "exploit_scorer": {
                "description": "Exploitability assessment",
                "methods": ["cvss_computation", "pattern_matching", "llm_scoring"],
                "input": "vulnerability findings",
                "output": "scored vulnerabilities with CVSS"
            }
        }
        
        cap = capabilities.get(agent_name, {
            "description": "Agent not found",
            "methods": [],
            "input": "unknown",
            "output": "unknown"
        })
        
        return {
            "agent_name": agent_name,
            "capabilities": cap,
            "available": agent_name in capabilities
        }
    
    def _explain_vulnerability(self, args: dict, context: dict = None) -> dict:
        """Handle explain_vulnerability tool."""
        cwe_id = args.get("cwe_id")
        context_info = args.get("context", "")
        
        if not cwe_id:
            raise ValueError("cwe_id is required")
        
        prompt = f"""Explain this vulnerability in detail:
        CWE: {cwe_id}
        Context: {context_info}
        
        Provide:
        1. Description of the vulnerability
        2. Real-world examples
        3. Attack vectors
        4. Mitigation strategies
        5. Code examples (vulnerable and fixed)"""
        
        explanation = self.llm.query(
            system="You are a security educator. Provide clear, practical explanations.",
            user=prompt,
            model="strong"
        )
        
        return {
            "cwe_id": cwe_id,
            "explanation": explanation,
            "generated_at": self._get_timestamp()
        }
    
    # ============================================
    # UTILITY METHODS
    # ============================================
    
    def _get_timestamp(self) -> str:
        """Get ISO timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
    
    def _is_json(self, text: str) -> bool:
        """Check if text is valid JSON."""
        try:
            json.loads(text)
            return True
        except:
            return False


# ============================================
# MCP PROTOCOL HANDLER (JSON-RPC STYLE)
# ============================================

class MCPProtocolHandler:
    """
    Handles MCP messages in JSON-RPC 2.0 format.
    This is the standard interface for MCP communication.
    """
    
    def __init__(self, server: MCPServer):
        self.server = server
    
    def handle_request(self, request: dict) -> dict:
        """
        Handle an MCP request (JSON-RPC 2.0).
        
        Request format:
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {...}
        }
        """
        jsonrpc = request.get("jsonrpc")
        if jsonrpc != "2.0":
            return self._error_response(request.get("id"), -32600, "Invalid Request")
        
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        if method == "initialize":
            return self._initialize(request_id, params)
        elif method == "tools/list":
            return self._tools_list(request_id)
        elif method == "tools/call":
            return self._tools_call(request_id, params)
        elif method == "resources/list":
            return self._resources_list(request_id)
        else:
            return self._error_response(request_id, -32601, f"Method not found: {method}")
    
    def _initialize(self, request_id, params):
        """Handle initialize method."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": "Multi-Agent Security Scanner MCP Server",
                    "version": "1.0.0"
                },
                "capabilities": {
                    "tools": True,
                    "resources": True
                }
            }
        }
    
    def _tools_list(self, request_id):
        """Handle tools/list method."""
        tools = self.server.list_tools()
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": tools
            }
        }
    
    def _tools_call(self, request_id, params):
        """Handle tools/call method."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        context = params.get("_meta", {})
        
        result = self.server.call_tool(tool_name, arguments, context)
        
        if "error" in result:
            return self._error_response(request_id, -32000, result["error"].get("message", "Tool error"))
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
    
    def _resources_list(self, request_id):
        """Handle resources/list method."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "resources": [
                    {
                        "uri": "memory://patterns",
                        "name": "Vulnerability Patterns",
                        "description": "Stored vulnerability patterns"
                    },
                    {
                        "uri": "memory://patches",
                        "name": "Patch History",
                        "description": "Previously generated patches"
                    }
                ]
            }
        }
    
    def _error_response(self, request_id, code, message):
        """Create JSON-RPC error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }


# Singleton instance
_mcp_server = None

def get_mcp_server() -> MCPServer:
    """Get or create MCP server instance."""
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPServer()
    return _mcp_server

def get_protocol_handler() -> MCPProtocolHandler:
    """Get MCP protocol handler."""
    return MCPProtocolHandler(get_mcp_server())