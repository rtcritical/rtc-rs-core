use std::fs;

fn load_case_ids() -> Vec<String> {
    let txt = fs::read_to_string("harness/parity/vectors_v0.json").expect("vectors file");
    let v: serde_json::Value = serde_json::from_str(&txt).expect("valid json");
    v.as_array()
        .expect("array")
        .iter()
        .map(|c| c.get("id").and_then(|x| x.as_str()).unwrap_or("unknown").to_string())
        .collect()
}

#[test]
fn parity_vectors_load() {
    let ids = load_case_ids();
    assert!(!ids.is_empty(), "expected non-empty vector pack");
}

#[test]
#[ignore = "stub not implemented"]
fn strict_abi_runner_stub() {
    let runner_ready = false;
    assert!(!runner_ready, "stub intentionally not implemented yet");
}

#[test]
#[ignore = "stub not implemented"]
fn comparator_stub() {
    let comparator_ready = false;
    assert!(!comparator_ready, "stub intentionally not implemented yet");
}
