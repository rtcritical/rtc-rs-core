use rtc_rs_core::core::Value;
use rtc_rs_core::api::{assoc_in, get_in, update_in};
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
    let r1 = assoc_in(&root, &["cfg", "http", "port"], Value::I64(8080)).unwrap();
    let got = get_in(&r1, &["cfg", "http", "port"]).unwrap();
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
    let out = update_in(&root, &["cfg", "port"], inc_nil).unwrap();
    let got = get_in(&out, &["cfg", "port"]).unwrap();
    assert_eq!(got, Value::I64(1));
}


#[test]
fn constructor_helpers_smoke() {
    use rtc_rs_core::api::{nil, b, i64v, f64v, s, vecv, mapv};
    assert_eq!(nil(), Value::Nil);
    assert_eq!(b(true), Value::Bool(true));
    assert_eq!(i64v(7), Value::I64(7));
    assert_eq!(f64v(1.5), Value::F64(1.5));
    assert_eq!(s("x"), Value::Str("x".into()));
    assert_eq!(vecv(vec![i64v(1)]), Value::Vec(vec![Value::I64(1)]));
    assert_eq!(mapv(vec![("k".into(), i64v(1))]), Value::Map(vec![("k".into(), Value::I64(1))]));
}
