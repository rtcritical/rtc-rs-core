use rtc_rs_core::{update, update_in, Key, Value};

fn nil_to_one(v: Value) -> Result<Value, rtc_rs_core::rtc_status> {
    Ok(match v {
        Value::Nil => Value::I64(1),
        Value::I64(n) => Value::I64(n + 1),
        _ => Value::Nil,
    })
}

#[test]
fn update_missing_applies_to_nil() {
    let root = Value::Map(vec![]);
    let out = update(&root, &Key::Str("x".into()), nil_to_one).unwrap();
    assert_eq!(out, Value::Map(vec![("x".into(), Value::I64(1))]));
}

#[test]
fn update_in_missing_applies_to_nil() {
    let root = Value::Map(vec![]);
    let out = update_in(&root, &[Key::Str("cfg".into()), Key::Str("port".into())], nil_to_one).unwrap();
    assert_eq!(out, Value::Map(vec![("cfg".into(), Value::Map(vec![("port".into(), Value::I64(1))]))]));
}
