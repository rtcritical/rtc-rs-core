use rtc_rs_core::{assoc, assoc_in, Key, Value};

#[test]
fn assoc_map_sets_key() {
    let root = Value::Map(vec![]);
    let out = assoc(&root, &Key::Str("a".into()), Value::I64(1)).unwrap();
    assert_eq!(out, Value::Map(vec![("a".into(), Value::I64(1))]));
}

#[test]
fn assoc_in_creates_nested_path() {
    let root = Value::Map(vec![]);
    let out = assoc_in(
        &root,
        &[Key::Str("cfg".into()), Key::Str("http".into()), Key::Str("port".into())],
        Value::I64(8080),
    )
    .unwrap();
    assert_eq!(
        out,
        Value::Map(vec![(
            "cfg".into(),
            Value::Map(vec![("http".into(), Value::Map(vec![("port".into(), Value::I64(8080))]))]),
        )])
    );
}
