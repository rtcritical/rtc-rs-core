use rtc_rs_core::api;
use rtc_rs_core::m;
use rtc_rs_core::core::{self, Key, Value, rtc_status};
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

fn run_case(id: &str) -> (rtc_status, Value) {
    match id {
        "vector_01_missing_top_key" => {
            let root = Value::Map(vec![]);
            let out = core::get_in(&root, &[Key::Str("missing".into())]).unwrap();
            (rtc_status::RTC_OK, out)
        }
        "vector_03_assoc_in_create_path" => {
            let root = Value::Map(vec![]);
            let out = core::assoc_in(
                &root,
                &[Key::Str("cfg".into()), Key::Str("http".into()), Key::Str("port".into())],
                Value::I64(8080),
            )
            .unwrap();
            (rtc_status::RTC_OK, out)
        }
        "vector_05_type_conflict" => {
            let root = Value::Map(vec![("a".into(), Value::I64(1))]);
            match core::get_in(&root, &[Key::Str("a".into()), Key::Str("b".into())]) {
                Ok(v) => (rtc_status::RTC_OK, v),
                Err(e) => (e, Value::Nil),
            }
        }
        _ => (rtc_status::RTC_ERR_INTERNAL, Value::Nil),
    }
}

#[test]
fn parity_vectors_load() {
    let ids = load_case_ids();
    assert!(!ids.is_empty(), "expected non-empty vector pack");
}

#[test]
fn parity_runner_executes_all_vectors() {
    for id in load_case_ids() {
        let (st, _out) = run_case(&id);
        assert_ne!(st, rtc_status::RTC_ERR_INTERNAL, "unknown vector id: {id}");
    }
}

#[test]
fn parity_api_vs_core_for_string_paths() {
    let root = Value::Map(vec![]);
    let via_api = api::nassoc_in(&root, &["cfg", "http", "port"], Value::I64(8080)).unwrap();
    let via_core = core::assoc_in(
        &root,
        &[Key::Str("cfg".into()), Key::Str("http".into()), Key::Str("port".into())],
        Value::I64(8080),
    )
    .unwrap();
    assert_eq!(via_api, via_core);
}


#[test]
fn parity_m_macro_vs_m_from() {
    let via_macro = m!(("a", Value::I64(1)), ("b", Value::I64(2)));
    let via_from = api::m_from(vec![("a", Value::I64(1)), ("b", Value::I64(2))]);
    assert_eq!(via_macro, via_from);
}
