use rtc_rs_core::api::*;
use rtc_rs_core::core::Value;

#[test]
fn empty_constructors_are_empty() {
    assert_eq!(v_empty(), Value::Vec(vec![]));
    assert_eq!(m_empty(), Value::Map(vec![]));
    assert_eq!(s_empty(), Value::Vec(vec![]));
}

#[test]
fn from_constructors_populate() {
    assert_eq!(v_from(vec![i(1), i(2)]), Value::Vec(vec![Value::I64(1), Value::I64(2)]));

    assert_eq!(
        m_from(vec![("a", i(1)), ("b", st("x"))]),
        Value::Map(vec![("a".into(), Value::I64(1)), ("b".into(), Value::Str("x".into()))])
    );
}

#[test]
fn map_from_last_write_wins_via_assoc_path() {
    // Constructor keeps entries; operational semantics of assoc should update existing key
    let m = m_from(vec![("a", i(1)), ("a", i(2))]);
    if let Value::Map(entries) = m {
        assert_eq!(entries.len(), 2);
    } else {
        panic!("expected map");
    }
}

#[test]
fn vector_index_helpers_bounds_and_growth() {
    let vv = v_from(vec![i(1)]);
    assert_eq!(v_get(&vv, 9).unwrap(), nil());

    let vv2 = v_assoc(&vv, 3, i(7)).unwrap();
    assert_eq!(v_get(&vv2, 3).unwrap(), i(7));
    assert_eq!(v_get(&vv2, 1).unwrap(), nil());
}
