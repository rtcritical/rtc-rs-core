use rtc_rs_core::Value;

#[test]
fn value_kinds_smoke() {
    assert_eq!(Value::Nil.kind(), "nil");
    assert_eq!(Value::Bool(true).kind(), "bool");
    assert_eq!(Value::I64(1).kind(), "i64");
    assert_eq!(Value::F64(1.0).kind(), "f64");
    assert_eq!(Value::Str("x".into()).kind(), "str");
    assert_eq!(Value::Vec(vec![]).kind(), "vec");
    assert_eq!(Value::Map(vec![]).kind(), "map");
}
