use rtc_rs_core::{get, get_in, Key, Value};

#[test]
fn get_missing_map_key_returns_nil() {
    let root = Value::Map(vec![("a".into(), Value::I64(1))]);
    let out = get(&root, &Key::Str("missing".into())).unwrap();
    assert_eq!(out, Value::Nil);
}

#[test]
fn get_in_nested_reads_value() {
    let root = Value::Map(vec![(
        "cfg".into(),
        Value::Map(vec![("http".into(), Value::Map(vec![("port".into(), Value::I64(8080))]))]),
    )]);
    let out = get_in(
        &root,
        &[
            Key::Str("cfg".into()),
            Key::Str("http".into()),
            Key::Str("port".into()),
        ],
    )
    .unwrap();
    assert_eq!(out, Value::I64(8080));
}

#[test]
fn get_in_type_conflict_errors() {
    let root = Value::Map(vec![("a".into(), Value::I64(1))]);
    let err = get_in(&root, &[Key::Str("a".into()), Key::Str("b".into())]).unwrap_err();
    assert_eq!(err as i32, rtc_rs_core::rtc_status::RTC_ERR_TYPE as i32);
}
