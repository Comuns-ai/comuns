import sys
base = sys.argv[1]  # S9 dir
crate = base + "/crate/"

p = crate + "Cargo.toml"
s = open(p).read()
old = 'futures = { version = "=0.3.34", default-features = false, features = ["std"] }\n'
assert s.count(old) == 1
s = s.replace(old, old + '''# S9 test (c) only: hand-build a response with an injected zero-length non-final chunk.
# Same versions ohttp 0.8.0 already resolves (no new crates in the graph).
chacha20poly1305 = { version = "=0.11.0", default-features = false }
hkdf = { version = "=0.13.0", default-features = false }
sha2 = { version = "=0.11.1", default-features = false }
''')
s += '''
# S9: ohttp 0.8.0 with the chunked fixes (nonce buffer, zero-length chunks).
[patch.crates-io]
ohttp = { path = "../ohttp-0.8.0-patched" }
'''
open(p, "w").write(s)

p = crate + "src/lib.rs"
s = open(p).read()


def rep(old, new):
    global s
    assert s.count(old) == 1, old[:80]
    s = s.replace(old, new)


start = s.index("/// Test (b) with the fixed suite (ChaCha20-Poly1305).")
end = s.index("/// Diagnostic only (NOT the fixed suite)")
s = s[:start] + open(base + "/src-edit/new_tests.rs").read() + s[end:]

rep('''    let a = roundtrip_a();
    let b = roundtrip_b();
    let diag = match roundtrip_b_aes_diagnostic() {
        Ok(d) => format!("diagnostic {d}"),
        Err(e) => format!("diagnostic FAIL {e}"),
    };
    match (a, b) {
        (Ok(a), Ok(b)) => format!("PASS {a}; {b}; {diag}"),
        (Ok(a), Err(b)) => format!("FAIL(b) {a}; {b}; {diag}"),
        (a, b) => format!("FAIL a={a:?} b={b:?}; {diag}"),
    }''', '''    let results = [
        ("a", roundtrip_a()),
        ("b", roundtrip_b()),
        ("c", roundtrip_c()),
        ("d", roundtrip_d()),
    ];
    let diag = match roundtrip_b_aes_diagnostic() {
        Ok(d) => format!("diagnostic {d}"),
        Err(e) => format!("diagnostic FAIL {e}"),
    };
    let failed: Vec<&str> = results
        .iter()
        .filter(|(_, r)| r.is_err())
        .map(|(n, _)| *n)
        .collect();
    let body: Vec<String> = results
        .iter()
        .map(|(n, r)| match r {
            Ok(s) => s.clone(),
            Err(e) => format!("{n} FAILED: {e}"),
        })
        .collect();
    let head = if failed.is_empty() {
        "PASS".to_string()
    } else {
        format!("FAIL({})", failed.join(","))
    };
    format!("{head} {}; {diag}", body.join("; "))''')
rep("    /// Runs chunked test (b) with ChaCha20-Poly1305 unguarded (expected to trap).",
    "    /// Runs chunked test (b) with ChaCha20-Poly1305 on its own.")
rep('''    #[test]
    fn test_b_aes128gcm_diagnostic() {''', '''    #[test]
    fn test_c_empty_nonfinal_chunk_rejected() {
        let r = roundtrip_c().unwrap();
        println!("{r}");
    }

    #[test]
    fn test_d_empty_write_emits_nothing() {
        let r = roundtrip_d().unwrap();
        println!("{r}");
    }

    #[test]
    fn test_b_aes128gcm_diagnostic() {''')
open(p, "w").write(s)
print("edited")
