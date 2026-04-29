use crate::core::{self, Key, Value, UpdaterFn, rtc_status};

pub fn get_in(root: &Value, path: &[&str]) -> Result<Value, rtc_status> {
    let ks: Vec<Key> = path.iter().map(|s| Key::Str((*s).to_string())).collect();
    core::get_in(root, &ks)
}

pub fn assoc_in(root: &Value, path: &[&str], val: Value) -> Result<Value, rtc_status> {
    let ks: Vec<Key> = path.iter().map(|s| Key::Str((*s).to_string())).collect();
    core::assoc_in(root, &ks, val)
}

pub fn update_in(root: &Value, path: &[&str], f: UpdaterFn) -> Result<Value, rtc_status> {
    let ks: Vec<Key> = path.iter().map(|s| Key::Str((*s).to_string())).collect();
    core::update_in(root, &ks, f)
}

pub fn k<S: Into<String>>(s: S) -> Key { Key::Str(s.into()) }
pub fn i(n: i64) -> Key { Key::Index(n) }
