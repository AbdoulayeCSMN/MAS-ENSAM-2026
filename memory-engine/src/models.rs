use serde::{Deserialize, Serialize};

/// Severity levels aligned with Python AgentState Severity enum
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
#[serde(rename_all = "lowercase")]
pub enum Severity {
    Info,
    Low,
    Medium,
    High,
    Critical,
}

impl std::fmt::Display for Severity {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Severity::Critical => write!(f, "critical"),
            Severity::High => write!(f, "high"),
            Severity::Medium => write!(f, "medium"),
            Severity::Low => write!(f, "low"),
            Severity::Info => write!(f, "info"),
        }
    }
}

/// A single memory vulnerability finding
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Finding {
    /// UUID v4
    pub id: String,
    /// Short title
    pub title: String,
    /// Severity level
    pub severity: Severity,
    /// CWE identifier e.g. "CWE-121"
    pub cwe: String,
    /// CVE if applicable
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cve: Option<String>,
    /// Relative file path from repo root
    pub file: String,
    /// 1-based start line
    pub line_start: usize,
    /// 1-based end line
    pub line_end: usize,
    /// Code snippet (the offending line ± context)
    pub snippet: String,
    /// Detailed description and remediation advice
    pub description: String,
    /// The pattern rule that triggered this finding
    pub rule_id: String,
}

/// Top-level JSON output consumed by memory_safety.py
#[derive(Debug, Serialize, Deserialize)]
pub struct ScanOutput {
    pub findings: Vec<Finding>,
    pub stats: ScanStats,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ScanStats {
    pub files_scanned: usize,
    pub total_findings: usize,
    pub by_severity: BySeverity,
}

#[derive(Debug, Serialize, Deserialize, Default)]
pub struct BySeverity {
    pub critical: usize,
    pub high: usize,
    pub medium: usize,
    pub low: usize,
    pub info: usize,
}

impl BySeverity {
    pub fn increment(&mut self, sev: &Severity) {
        match sev {
            Severity::Critical => self.critical += 1,
            Severity::High => self.high += 1,
            Severity::Medium => self.medium += 1,
            Severity::Low => self.low += 1,
            Severity::Info => self.info += 1,
        }
    }
}
