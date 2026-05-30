/// Pattern-based rule definition
#[derive(Debug, Clone)]
pub struct Rule {
    pub id: &'static str,
    pub title: &'static str,
    pub cwe: &'static str,
    pub severity: crate::models::Severity,
    /// Regex pattern to match against a single source line
    pub pattern: &'static str,
    /// Short description + remediation
    pub description: &'static str,
    /// Languages this rule applies to
    pub languages: &'static [Language],
}

#[derive(Debug, Clone, PartialEq)]
pub enum Language {
    C,
    Cpp,
    Rust,
}

use crate::models::Severity;

/// All memory safety rules
pub fn all_rules() -> Vec<Rule> {
    vec![
        // ── Buffer Overflow ──────────────────────────────────────────────────
        Rule {
            id: "MEM-001",
            title: "Use of unsafe strcpy — stack buffer overflow risk",
            cwe: "CWE-121",
            severity: Severity::Critical,
            pattern: r"\bstrcpy\s*\(",
            description: "strcpy does not check destination buffer size. \
                Replace with strncpy(dst, src, sizeof(dst)-1) or strlcpy. \
                An attacker supplying oversized input can overwrite adjacent memory.",
            languages: &[Language::C, Language::Cpp],
        },
        Rule {
            id: "MEM-002",
            title: "Use of unsafe strcat — buffer overflow risk",
            cwe: "CWE-120",
            severity: Severity::Critical,
            pattern: r"\bstrcat\s*\(",
            description: "strcat appends without bounds checking. \
                Use strncat(dst, src, sizeof(dst)-strlen(dst)-1) or strlcat.",
            languages: &[Language::C, Language::Cpp],
        },
        Rule {
            id: "MEM-003",
            title: "Use of gets — unbounded input, always a buffer overflow",
            cwe: "CWE-242",
            severity: Severity::Critical,
            pattern: r"\bgets\s*\(",
            description: "gets() is banned (C11 removed it). \
                Use fgets(buf, sizeof(buf), stdin) instead.",
            languages: &[Language::C, Language::Cpp],
        },
        Rule {
            id: "MEM-004",
            title: "Use of unsafe sprintf — format string buffer overflow",
            cwe: "CWE-134",
            severity: Severity::High,
            pattern: r"\bsprintf\s*\(",
            description: "sprintf writes without bounds checking. \
                Replace with snprintf(buf, sizeof(buf), fmt, ...) \
                to prevent output truncation or overflow.",
            languages: &[Language::C, Language::Cpp],
        },
        Rule {
            id: "MEM-005",
            title: "Use of scanf with unbounded %s",
            cwe: "CWE-121",
            severity: Severity::High,
            pattern: r#"\bscanf\s*\(\s*"[^"]*%s"#,
            description: "scanf(\"%s\", ...) reads until whitespace with no length limit. \
                Use scanf(\"%255s\", ...) or fgets instead.",
            languages: &[Language::C, Language::Cpp],
        },

        // ── Use After Free ───────────────────────────────────────────────────
        Rule {
            id: "MEM-010",
            title: "Potential use-after-free: free() followed by pointer use",
            cwe: "CWE-416",
            severity: Severity::Critical,
            pattern: r"\bfree\s*\(\s*\w+\s*\)",
            description: "After free(), the pointer is dangling. Set it to NULL immediately: \
                free(ptr); ptr = NULL; \
                Accessing it afterward is undefined behavior and exploitable.",
            languages: &[Language::C, Language::Cpp],
        },
        Rule {
            id: "MEM-011",
            title: "Double-free risk: free() called more than once on same pointer",
            cwe: "CWE-415",
            severity: Severity::Critical,
            pattern: r"\bfree\s*\(",
            description: "Calling free() twice on the same pointer corrupts the heap. \
                Set pointer to NULL after first free to prevent accidental double-free.",
            languages: &[Language::C, Language::Cpp],
        },

        // ── Memory Leaks ─────────────────────────────────────────────────────
        Rule {
            id: "MEM-020",
            title: "malloc/calloc result not checked for NULL",
            cwe: "CWE-252",
            severity: Severity::High,
            pattern: r"\b(malloc|calloc|realloc)\s*\(",
            description: "Allocation functions return NULL on failure. \
                Always check: ptr = malloc(n); if (!ptr) { /* handle */ } \
                Ignoring NULL leads to null pointer dereference.",
            languages: &[Language::C, Language::Cpp],
        },
        Rule {
            id: "MEM-021",
            title: "Memory allocated on heap without corresponding free",
            cwe: "CWE-401",
            severity: Severity::Medium,
            pattern: r"\bnew\s+\w",
            description: "C++ 'new' allocates heap memory. Ensure every 'new' has a matching 'delete'. \
                Prefer RAII containers (std::unique_ptr, std::vector) to avoid leaks.",
            languages: &[Language::Cpp],
        },

        // ── Null Pointer Dereference ─────────────────────────────────────────
        Rule {
            id: "MEM-030",
            title: "Null pointer dereference risk: pointer used without NULL check",
            cwe: "CWE-476",
            severity: Severity::High,
            pattern: r"\*\s*\w+\s*=\s*NULL",
            description: "Dereferencing a NULL pointer causes a segmentation fault. \
                Always validate pointers before use: if (ptr != NULL) { ... }",
            languages: &[Language::C, Language::Cpp],
        },

        // ── Integer Overflow ─────────────────────────────────────────────────
        Rule {
            id: "MEM-040",
            title: "Integer overflow risk in size calculation for allocation",
            cwe: "CWE-190",
            severity: Severity::High,
            pattern: r"\bmalloc\s*\(\s*\w+\s*\*\s*\w+",
            description: "Multiplying sizes before malloc can overflow. \
                Use calloc(n, sizeof(T)) or check for overflow: \
                if (n > SIZE_MAX / sizeof(T)) { /* overflow */ }",
            languages: &[Language::C, Language::Cpp],
        },

        // ── Format String ────────────────────────────────────────────────────
        Rule {
            id: "MEM-050",
            title: "Uncontrolled format string",
            cwe: "CWE-134",
            severity: Severity::Critical,
            pattern: r"\b(printf|fprintf|syslog)\s*\(\s*\w+\s*\)",
            description: "Passing a user-controlled string directly as format argument. \
                Use printf(\"%s\", user_input) — never printf(user_input).",
            languages: &[Language::C, Language::Cpp],
        },

        // ── Stack Smashing ───────────────────────────────────────────────────
        Rule {
            id: "MEM-060",
            title: "Variable-length array (VLA) — stack overflow risk",
            cwe: "CWE-770",
            severity: Severity::Medium,
            pattern: r"\w+\s+\w+\s*\[\s*\w+\s*\]\s*;",
            description: "C99 VLAs allocate on the stack with no overflow check. \
                Large or attacker-controlled sizes can smash the stack. \
                Use malloc/calloc for dynamic sizes.",
            languages: &[Language::C, Language::Cpp],
        },

        // ── Unsafe Rust ──────────────────────────────────────────────────────
        Rule {
            id: "MEM-070",
            title: "Unsafe block: raw pointer dereference",
            cwe: "CWE-119",
            severity: Severity::High,
            pattern: r"\bunsafe\s*\{",
            description: "Unsafe blocks bypass Rust's memory safety guarantees. \
                Ensure all raw pointer operations are bounds-checked and lifetimes are valid. \
                Document invariants and consider using safe abstractions.",
            languages: &[Language::Rust],
        },
        Rule {
            id: "MEM-071",
            title: "Use of std::mem::transmute — type safety bypass",
            cwe: "CWE-843",
            severity: Severity::High,
            pattern: r"\bmem::transmute\s*[:<]",
            description: "transmute reinterprets memory with no type checks. \
                This can create invalid references or misaligned access. \
                Use safe casting (as, From/Into) wherever possible.",
            languages: &[Language::Rust],
        },
        Rule {
            id: "MEM-072",
            title: "Use of std::ptr::read/write — unsafe memory access",
            cwe: "CWE-125",
            severity: Severity::High,
            pattern: r"\bptr::(read|write|copy)\b",
            description: "Raw pointer read/write bypasses borrow checker. \
                Verify alignment, validity and lifetime before use.",
            languages: &[Language::Rust],
        },
        Rule {
            id: "MEM-073",
            title: "Box::from_raw — ownership invariant violation risk",
            cwe: "CWE-416",
            severity: Severity::High,
            pattern: r"\bBox::from_raw\s*\(",
            description: "Box::from_raw takes ownership of a raw pointer. \
                Double-free if called more than once on the same pointer. \
                Ensure only one Box owns the allocation.",
            languages: &[Language::Rust],
        },
        Rule {
            id: "MEM-074",
            title: "Use of std::slice::from_raw_parts — out-of-bounds risk",
            cwe: "CWE-125",
            severity: Severity::High,
            pattern: r"\bslice::from_raw_parts\b",
            description: "from_raw_parts creates a slice from a raw pointer and length. \
                If the length exceeds the actual allocation, reading is undefined behavior.",
            languages: &[Language::Rust],
        },

        // ── C++ Specific ─────────────────────────────────────────────────────
        Rule {
            id: "MEM-080",
            title: "Use of raw delete[] — mismatch with new risk",
            cwe: "CWE-401",
            severity: Severity::Medium,
            pattern: r"\bdelete\s*\[",
            description: "delete[] must match new[]. Mismatching new/delete or new[]/delete[] \
                is undefined behavior. Use std::vector or std::unique_ptr<T[]> instead.",
            languages: &[Language::Cpp],
        },
        Rule {
            id: "MEM-081",
            title: "memcpy with potentially overlapping buffers",
            cwe: "CWE-119",
            severity: Severity::Medium,
            pattern: r"\bmemcpy\s*\(",
            description: "memcpy has undefined behavior for overlapping regions. \
                Use memmove if source and destination may overlap.",
            languages: &[Language::C, Language::Cpp],
        },
    ]
}
