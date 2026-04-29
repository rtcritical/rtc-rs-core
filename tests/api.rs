use rtc_rs_core::core::Value;
use rtc_rs_core::api::{assoc_in, get_in, update_in, nil, b, i, f, st, v_from, s_from, m, m_from, v_get, v_assoc, idx};
use rtc_rs_core::{path, path_mixed, v, s};

fn inc_nil(v: Value) -> Result<Value, rtc_rs_core::rtc_status> {
    Ok(match v {
        Value::Nil => i(1),
        Value::I64(n) => Value::I64(n + 1),
        _ => Value::Nil,
    })
}

#[test]
fn short_str_path_helpers_work() {
    let root = m();
    let r1 = assoc_in(&root, &["cfg", "http", "port"], i(8080)).unwrap();
    let got = get_in(&r1, &["cfg", "http", "port"]).unwrap();
    assert_eq!(got, i(8080));
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
    let root = m();
    let out = update_in(&root, &["cfg", "port"], inc_nil).unwrap();
    let got = get_in(&out, &["cfg", "port"]).unwrap();
    assert_eq!(got, i(1));
}


#[test]
fn constructor_helpers_smoke() {
    assert_eq!(nil(), Value::Nil);
    assert_eq!(b(true), Value::Bool(true));
    assert_eq!(i(7), Value::I64(7));
    assert_eq!(f(1.5), Value::F64(1.5));
    assert_eq!(st("x"), Value::Str("x".into()));
    assert_eq!(v!(), Value::Vec(vec![]));
    assert_eq!(v_from(vec![i(1)]), Value::Vec(vec![Value::I64(1)]));
    assert_eq!(m(), Value::Map(vec![]));
    assert_eq!(m_from(vec![("k", i(1))]), Value::Map(vec![("k".into(), Value::I64(1))]));
    assert_eq!(s!(), Value::Vec(vec![]));
    assert_eq!(s_from(vec![i(2)]), Value::Vec(vec![Value::I64(2)]));
}


#[test]
fn v_index_helpers_work() {
    let vv = v_from(vec![i(1), i(2)]);
    assert_eq!(v_get(&vv, 1).unwrap(), i(2));
    let vv2 = v_assoc(&vv, 0, i(9)).unwrap();
    assert_eq!(v_get(&vv2, 0).unwrap(), i(9));
    // still possible to build explicit mixed key when needed
    let _k = idx(3);
}


#[test]
fn keys_vals_helpers_smoke() {
    use rtc_rs_core::api::vals;
    let mm = m_from(vec![("a", i(1)), ("b", i(2))]);
    if let Value::Map(entries) = mm {
        let vv = vals(&entries);
        assert_eq!(vv.len(), 2);
        assert_eq!(*vv[0], i(1));
    } else {
        panic!("expected map");
    }
}


#[test]
fn keys_helper_builds_path_keys() {
    let p = path!["cfg", "http", "port"];
    assert_eq!(p.len(), 3);
}
