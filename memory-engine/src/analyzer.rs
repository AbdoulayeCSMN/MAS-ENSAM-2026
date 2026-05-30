use std::path::{Path, PathBuf};

use once_cell::sync::Lazy;
use regex::Regex;
use uuid::Uuid;
use walkdir::WalkDir;

use crate::models::Finding;
use crate::rules::{all_rules, Language, Rule};

/// Extensions recognized per language
fn language_for_ext(ext: &str) -> Option<Language> {
    match ext {
        "c" | "h" => Some(Language::C),
        "cpp" | "cc" | "cxx" | "hpp" | "hxx" | "hh" => Some(Language::Cpp),
        "rs" => Some(Language::Rust),
        _ => None,
    }
}

/// Directories to skip during traversal
const SKIP_DIRS: &[&str] = &[
    ".git",
    "node_modules",
    "__pycache__",
    "target",
    "build",
    "dist",
    ".cache",
    "vendor",
    "third_party",
    "external",
];

/// Scan a whole repository and return all findings
pub fn scan_repository(repo_root: &Path) -> (Vec<Finding>, usize) {
    let rules = all_rules();
    let mut findings: Vec<Finding> = Vec::new();
    let mut files_scanned = 0usize;

    for entry in WalkDir::new(repo_root)
        .follow_links(false)
        .into_iter()
        .filter_entry(|e| {
            // Skip unwanted directories
            if e.file_type().is_dir() {
                let name = e.file_name().to_string_lossy();
                return !SKIP_DIRS.contains(&name.as_ref());
            }
            true
        })
        .filter_map(|e| e.ok())
        .filter(|e| e.file_type().is_file())
    {
        let path = entry.path();
        let ext = path
            .extension()
            .and_then(|e| e.to_str())
            .unwrap_or("")
            .to_lowercase();

        let Some(lang) = language_for_ext(&ext) else {
            continue;
        };

        files_scanned += 1;

        let rel_path = path
            .strip_prefix(repo_root)
            .unwrap_or(path)
            .to_string_lossy()
            .replace('\\', "/");

        if let Ok(source) = std::fs::read_to_string(path) {
            let mut file_findings = analyze_file(&source, &rel_path, &lang, &rules);
            findings.append(&mut file_findings);
        }
    }

    // Sort by file then line for deterministic output
    findings.sort_by(|a, b| {
        a.file
            .cmp(&b.file)
            .then(a.line_start.cmp(&b.line_start))
    });

    (findings, files_scanned)
}

/// Analyze a single file's source text against applicable rules
fn analyze_file(source: &str, rel_path: &str, lang: &Language, rules: &[Rule]) -> Vec<Finding> {
    let lines: Vec<&str> = source.lines().collect();
    let mut findings: Vec<Finding> = Vec::new();

    for rule in rules {
        // Only apply rule if language matches
        if !rule.languages.contains(lang) {
            continue;
        }

        let Ok(re) = Regex::new(rule.pattern) else {
            continue;
        };

        // Track if we already reported this rule for this line (avoid duplicates)
        let mut reported_lines: std::collections::HashSet<usize> = std::collections::HashSet::new();

        for (idx, line) in lines.iter().enumerate() {
            // Skip comment-only lines
            let trimmed = line.trim();
            if trimmed.starts_with("//")
                || trimmed.starts_with('#')
                || trimmed.starts_with('*')
                || trimmed.starts_with("/*")
            {
                continue;
            }

            if re.is_match(line) {
                let line_number = idx + 1; // 1-based

                if reported_lines.contains(&line_number) {
                    continue;
                }
                reported_lines.insert(line_number);

                let snippet = build_snippet(&lines, idx, 2);

                findings.push(Finding {
                    id: Uuid::new_v4().to_string(),
                    title: rule.title.to_string(),
                    severity: rule.severity.clone(),
                    cwe: rule.cwe.to_string(),
                    cve: None,
                    file: rel_path.to_string(),
                    line_start: line_number,
                    line_end: line_number,
                    snippet,
                    description: rule.description.to_string(),
                    rule_id: rule.id.to_string(),
                });
            }
        }
    }

    findings
}

/// Build a code snippet with `context` lines before and after
fn build_snippet(lines: &[&str], center: usize, context: usize) -> String {
    let start = center.saturating_sub(context);
    let end = (center + context + 1).min(lines.len());

    lines[start..end]
        .iter()
        .enumerate()
        .map(|(i, line)| {
            let lineno = start + i + 1;
            if start + i == center {
                format!(">{lineno:4} | {line}")
            } else {
                format!(" {lineno:4} | {line}")
            }
        })
        .collect::<Vec<_>>()
        .join("\n")
}
