use crate::core::{self, rtc_status, Key, UpdaterFn, Value};

// Value constructors (Rust-to-Rust ergonomic layer)
pub fn nil() -> Value { Value::Nil }
pub fn b(v: bool) -> Value { Value::Bool(v) }
pub fn i(v: i64) -> Value { Value::I64(v) }
pub fn f(v: f64) -> Value { Value::F64(v) }
pub fn st<S: Into<String>>(v: S) -> Value { Value::Str(v.into()) }

pub fn v_from<I>(iter: I) -> Value
where
    I: IntoIterator<Item = Value>,
{
    Value::Vec(iter.into_iter().collect())
}

// set is extension-oriented in current model; represented as vector until set type lands
pub fn s_from<I>(iter: I) -> Value
where
    I: IntoIterator<Item = Value>,
{
    Value::Vec(iter.into_iter().collect())
}

pub fn m_from_pairs<K>(pairs: Vec<(K, Value)>) -> Value
where
    K: Into<String>,
{
    Value::Map(pairs.into_iter().map(|(k, v)| (k.into(), v)).collect())
}
pub fn m_from<I, K>(iter: I) -> Value
where
    I: IntoIterator<Item = (K, Value)>,
    K: Into<String>,
{
    m_from_pairs(iter.into_iter().collect())
}



pub fn vals<'a>(m: &'a [(String, Value)]) -> Vec<&'a Value> {
    m.iter().map(|(_, v)| v).collect()
}

pub fn k<S: Into<String>>(s: S) -> Key { Key::Str(s.into()) }
pub fn idx(n: i64) -> Key { Key::Index(n) }

fn keys(path: &[&str]) -> Vec<Key> {
    path.iter().map(|s| k(*s)).collect()
}

pub fn get_in(root: &Value, path: &[&str]) -> Result<Value, rtc_status> {
    core::get_in(root, &keys(path))
}

pub fn assoc_in(root: &Value, path: &[&str], val: Value) -> Result<Value, rtc_status> {
    core::assoc_in(root, &keys(path), val)
}

pub fn update_in(root: &Value, path: &[&str], f: UpdaterFn) -> Result<Value, rtc_status> {
    core::update_in(root, &keys(path), f)
}

// optional explicit vector index helpers so most callers avoid Key::Index directly
pub fn v_get(root: &Value, idxv: i64) -> Result<Value, rtc_status> {
    core::get(root, &Key::Index(idxv))
}

pub fn v_assoc(root: &Value, idxv: i64, val: Value) -> Result<Value, rtc_status> {
    core::assoc(root, &Key::Index(idxv), val)
}

pub fn v_update(root: &Value, idxv: i64, f: UpdaterFn) -> Result<Value, rtc_status> {
    core::update(root, &Key::Index(idxv), f)
}
