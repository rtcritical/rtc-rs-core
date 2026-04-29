use crate::core::{self, rtc_status, Key, UpdaterFn, Value};

// Value constructors (Rust-to-Rust ergonomic layer)
pub fn nil() -> Value { Value::Nil }
pub fn b(v: bool) -> Value { Value::Bool(v) }
pub fn i64v(v: i64) -> Value { Value::I64(v) }
pub fn f64v(v: f64) -> Value { Value::F64(v) }
pub fn s<S: Into<String>>(v: S) -> Value { Value::Str(v.into()) }
pub fn vecv(v: Vec<Value>) -> Value { Value::Vec(v) }
pub fn mapv(v: Vec<(String, Value)>) -> Value { Value::Map(v) }

pub fn k<S: Into<String>>(s: S) -> Key { Key::Str(s.into()) }
pub fn i(n: i64) -> Key { Key::Index(n) }

fn ks(path: &[&str]) -> Vec<Key> {
    path.iter().map(|s| k(*s)).collect()
}

pub fn get_in(root: &Value, path: &[&str]) -> Result<Value, rtc_status> {
    core::get_in(root, &ks(path))
}

pub fn assoc_in(root: &Value, path: &[&str], val: Value) -> Result<Value, rtc_status> {
    core::assoc_in(root, &ks(path), val)
}

pub fn update_in(root: &Value, path: &[&str], f: UpdaterFn) -> Result<Value, rtc_status> {
    core::update_in(root, &ks(path), f)
}
