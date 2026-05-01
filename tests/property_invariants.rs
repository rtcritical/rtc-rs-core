use rtc_rs_core::core::{self, Key, Value};

fn inc_nil(v: Value) -> Result<Value, rtc_rs_core::rtc_status> {
    Ok(match v {
        Value::Nil => Value::I64(1),
        Value::I64(n) => Value::I64(n + 1),
        _ => Value::Nil,
    })
}

#[test]
fn prop_assoc_get_roundtrip_map_keys() {
    for i in 0..50 {
        let root = Value::Map(vec![]);
        let k = format!("k{i}");
        let v = Value::I64(i as i64);
        let out = core::assoc(&root, &Key::Str(k.clone()), v.clone()).unwrap();
        let got = core::get(&out, &Key::Str(k)).unwrap();
        assert_eq!(got, v);
    }
}

#[test]
fn prop_assoc_in_get_in_roundtrip_paths() {
    for i in 0..30 {
        let root = Value::Map(vec![]);
        let path = vec![Key::Str("cfg".into()), Key::Str(format!("p{i}"))];
        let v = Value::I64((i * 3) as i64);
        let out = core::assoc_in(&root, &path, v.clone()).unwrap();
        let got = core::get_in(&out, &path).unwrap();
        assert_eq!(got, v);
    }
}

#[test]
fn prop_update_in_nil_is_deterministic() {
    for _ in 0..20 {
        let root = Value::Map(vec![]);
        let path = vec![Key::Str("x".into()), Key::Str("y".into())];
        let out = core::update_in(&root, &path, inc_nil).unwrap();
        let got = core::get_in(&out, &path).unwrap();
        assert_eq!(got, Value::I64(1));
    }
}
