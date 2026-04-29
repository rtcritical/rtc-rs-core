use rtc_rs_core::{assoc_in_str, get_in_str, update_in_str, Value};
use rtc_rs_core::{path, path_mixed};

fn inc_nil(v: Value) -> Result<Value, rtc_rs_core::rtc_status> {
    Ok(match v {
        Value::Nil => Value::I64(1),
        Value::I64(n) => Value::I64(n + 1),
        _ => Value::Nil,
    })
}

#[test]
fn short_str_path_helpers_work() {
    let root = Value::Map(vec![]);
    let r1 = assoc_in_str(&root, &["cfg", "http", "port"], Value::I64(8080)).unwrap();
    let got = get_in_str(&r1, &["cfg", "http", "port"]).unwrap();
    assert_eq!(got, Value::I64(8080));
}

#[test]
fn path_macro_builds_keys() {
    let p = path!["a", "b", "c"];
    assert_eq!(p.len(), 3);
}

#[test]
fn path_mixed_supports_indices() {
    let p = path_mixed!["arr", [1], "x"];
    assert_eq!(p.len(), 3);
}

#[test]
fn update_in_str_nil_semantics() {
    let root = Value::Map(vec![]);
    let out = update_in_str(&root, &["cfg", "port"], inc_nil).unwrap();
    let got = get_in_str(&out, &["cfg", "port"]).unwrap();
    assert_eq!(got, Value::I64(1));
}
