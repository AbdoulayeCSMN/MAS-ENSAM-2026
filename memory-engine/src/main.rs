mod analyzer;
mod models;
mod rules;

use std::path::PathBuf;
use std::process;

use clap::Parser;
use colored::*;

use models::{BySeverity, ScanOutput, ScanStats};

/// Memory Safety Engine — static analyzer for C, C++ and Rust
#[derive(Parser, Debug)]
#[command(
    name = "memory-engine",
    version = "0.1.0",
    about = "Static memory safety analyzer for C, C++ and Rust source code",
    long_about = None
)]
struct Cli {
    /// Path to the repository root to scan
    #[arg(value_name = "REPO_PATH")]
    repo_path: PathBuf,

    /// Output results as JSON (required for Python agent integration)
    #[arg(long, default_value_t = false)]
    json: bool,

    /// Only report findings with severity >= this level (info|low|medium|high|critical)
    #[arg(long, default_value = "low")]
    min_severity: String,

    /// Show verbose progress output on stderr
    #[arg(short, long, default_value_t = false)]
    verbose: bool,
}

fn main() {
    let cli = Cli::parse();

    // Validate repo path
    if !cli.repo_path.exists() {
        eprintln!(
            "{} Repository path does not exist: {}",
            "ERROR".red().bold(),
            cli.repo_path.display()
        );
        process::exit(1);
    }

    if !cli.repo_path.is_dir() {
        eprintln!(
            "{} Path is not a directory: {}",
            "ERROR".red().bold(),
            cli.repo_path.display()
        );
        process::exit(1);
    }

    if cli.verbose {
        eprintln!(
            "{} Scanning: {}",
            "memory-engine".green().bold(),
            cli.repo_path.display()
        );
    }

    // Run the scan
    let (mut findings, files_scanned) = analyzer::scan_repository(&cli.repo_path);

    // Filter by minimum severity
    let min_sev = parse_severity(&cli.min_severity);
    findings.retain(|f| f.severity >= min_sev);

    // Build stats
    let mut by_severity = BySeverity::default();
    for f in &findings {
        by_severity.increment(&f.severity);
    }

    let total = findings.len();
    let stats = ScanStats {
        files_scanned,
        total_findings: total,
        by_severity,
    };

    if cli.verbose {
        eprintln!(
            "{} {} files scanned, {} findings",
            "memory-engine".green().bold(),
            files_scanned,
            total
        );
    }

    let output = ScanOutput { findings, stats };

    // JSON output — consumed by Python MemorySafetyAgent
    match serde_json::to_string_pretty(&output) {
        Ok(json) => println!("{json}"),
        Err(e) => {
            eprintln!("{} JSON serialization failed: {e}", "ERROR".red().bold());
            process::exit(2);
        }
    }
}

fn parse_severity(s: &str) -> models::Severity {
    match s.to_lowercase().as_str() {
        "critical" => models::Severity::Critical,
        "high" => models::Severity::High,
        "medium" => models::Severity::Medium,
        "low" => models::Severity::Low,
        _ => models::Severity::Info,
    }
}
