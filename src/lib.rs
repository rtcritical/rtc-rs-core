//! rtc-rs-core: Rust core for RTCritical hierarchical data model.

#![allow(non_camel_case_types)]

use std::ffi::{c_char, c_int};
use std::ptr;

#[derive(Clone, Debug, PartialEq)]
pub enum Value {
    Nil,
    Bool(bool),
    I64(i64),
    F64(f64),
    Str(String),
    Vec(Vec<Value>),
    Map(Vec<(String, Value)>), // order unspecified semantically
}

impl Value {
    pub fn kind(&self) -> &'static str {
        match self {
            Value::Nil => "nil",
            Value::Bool(_) => "bool",
            Value::I64(_) => "i64",
            Value::F64(_) => "f64",
            Value::Str(_) => "str",
            Value::Vec(_) => "vec",
            Value::Map(_) => "map",
        }
    }
}

#[derive(Clone, Debug, PartialEq)]
pub enum Key {
    Str(String),
    Index(i64),
}

pub fn get(root: &Value, key: &Key) -> Result<Value, rtc_status> {
    match (root, key) {
        (Value::Map(m), Key::Str(k)) => Ok(m.iter().find(|(mk, _)| mk == k).map(|(_, v)| v.clone()).unwrap_or(Value::Nil)),
        (Value::Vec(v), Key::Index(i)) => {
            if *i < 0 {
                return Ok(Value::Nil);
            }
            Ok(v.get(*i as usize).cloned().unwrap_or(Value::Nil))
        }
        (Value::Nil, _) => Ok(Value::Nil),
        _ => Err(rtc_status::RTC_ERR_TYPE),
    }
}

pub fn get_in(root: &Value, path: &[Key]) -> Result<Value, rtc_status> {
    let mut cur = root.clone();
    for k in path {
        cur = get(&cur, k)?;
        if matches!(cur, Value::Nil) {
            return Ok(Value::Nil);
        }
    }
    Ok(cur)
}

fn upsert_map_entries(mut m: Vec<(String, Value)>, k: String, v: Value) -> Vec<(String, Value)> {
    if let Some((_, mv)) = m.iter_mut().find(|(mk, _)| *mk == k) {
        *mv = v;
        return m;
    }
    m.push((k, v));
    m
}

pub fn assoc(root: &Value, key: &Key, val: Value) -> Result<Value, rtc_status> {
    match (root, key) {
        (Value::Map(m), Key::Str(k)) => Ok(Value::Map(upsert_map_entries(m.clone(), k.clone(), val))),
        (Value::Nil, Key::Str(k)) => Ok(Value::Map(vec![(k.clone(), val)])),
        (Value::Vec(v), Key::Index(i)) => {
            if *i < 0 {
                return Err(rtc_status::RTC_ERR_TYPE);
            }
            let idx = *i as usize;
            let mut out = v.clone();
            if idx >= out.len() {
                out.resize(idx + 1, Value::Nil);
            }
            out[idx] = val;
            Ok(Value::Vec(out))
        }
        (Value::Nil, Key::Index(i)) => {
            if *i < 0 {
                return Err(rtc_status::RTC_ERR_TYPE);
            }
            let idx = *i as usize;
            let mut out = vec![Value::Nil; idx + 1];
            out[idx] = val;
            Ok(Value::Vec(out))
        }
        _ => Err(rtc_status::RTC_ERR_TYPE),
    }
}

pub fn assoc_in(root: &Value, path: &[Key], val: Value) -> Result<Value, rtc_status> {
    if path.is_empty() {
        return Ok(val);
    }
    if path.len() == 1 {
        return assoc(root, &path[0], val);
    }
    let head = &path[0];
    let tail = &path[1..];
    let child = get(root, head)?;
    let child_base = if matches!(child, Value::Nil) {
        match tail.first() {
            Some(Key::Str(_)) => Value::Map(vec![]),
            Some(Key::Index(_)) => Value::Vec(vec![]),
            None => Value::Nil,
        }
    } else {
        child
    };
    let updated_child = assoc_in(&child_base, tail, val)?;
    assoc(root, head, updated_child)
}


#[repr(C)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum rtc_status {
    RTC_OK = 0,
    RTC_ERR_INVALID_ARG = 1,
    RTC_ERR_TYPE = 2,
    RTC_ERR_BOUNDS = 3,
    RTC_ERR_OOM = 4,
    RTC_ERR_OVERFLOW = 5,
    RTC_ERR_STATE = 6,
    RTC_ERR_INTERNAL = 7,
}

#[repr(C)]
pub enum rtc_key_kind {
    RTC_KEY_STR = 1,
    RTC_KEY_INDEX = 2,
}

#[repr(C)]
#[derive(Clone, Copy)]
pub struct rtc_str {
    pub ptr: *const c_char,
    pub len: u64,
}

#[repr(C)]
pub union rtc_key_as {
    pub str_: rtc_str,
    pub index: i64,
}

#[repr(C)]
pub struct rtc_key {
    pub kind: rtc_key_kind,
    pub as_: rtc_key_as,
}

#[repr(C)]
pub struct rtc_path {
    pub elems: *const rtc_key,
    pub len: u64,
}

#[repr(C)]
pub struct rtc_ctx {
    last_error_code: rtc_status,
    last_error_msg: String,
}

#[repr(C)]
pub struct rtc_val {
    inner: Value,
}

fn set_error(ctx: *mut rtc_ctx, code: rtc_status, msg: &str) {
    if ctx.is_null() {
        return;
    }
    unsafe {
        (*ctx).last_error_code = code;
        (*ctx).last_error_msg = msg.to_string();
    }
}

unsafe fn key_from_ffi(k: &rtc_key) -> Result<Key, rtc_status> {
    match k.kind {
        rtc_key_kind::RTC_KEY_STR => {
            let s = unsafe { k.as_.str_ };
            if s.ptr.is_null() {
                return Err(rtc_status::RTC_ERR_INVALID_ARG);
            }
            let bytes = unsafe { std::slice::from_raw_parts(s.ptr as *const u8, s.len as usize) };
            Ok(Key::Str(String::from_utf8_lossy(bytes).to_string()))
        }
        rtc_key_kind::RTC_KEY_INDEX => Ok(Key::Index(unsafe { k.as_.index })),
    }
}

#[unsafe(no_mangle)]
pub extern "C" fn rtc_ctx_new(out_ctx: *mut *mut rtc_ctx) -> rtc_status {
    if out_ctx.is_null() {
        return rtc_status::RTC_ERR_INVALID_ARG;
    }
    let ctx = Box::new(rtc_ctx {
        last_error_code: rtc_status::RTC_OK,
        last_error_msg: String::new(),
    });
    unsafe { *out_ctx = Box::into_raw(ctx) };
    rtc_status::RTC_OK
}

#[unsafe(no_mangle)]
pub extern "C" fn rtc_ctx_free(ctx: *mut rtc_ctx) -> rtc_status {
    if ctx.is_null() {
        return rtc_status::RTC_ERR_INVALID_ARG;
    }
    unsafe { drop(Box::from_raw(ctx)) };
    rtc_status::RTC_OK
}

#[unsafe(no_mangle)]
pub extern "C" fn rtc_last_error_code(ctx: *mut rtc_ctx) -> rtc_status {
    if ctx.is_null() {
        return rtc_status::RTC_ERR_INVALID_ARG;
    }
    unsafe { (*ctx).last_error_code }
}

#[unsafe(no_mangle)]
pub extern "C" fn rtc_last_error_message(ctx: *mut rtc_ctx) -> *const c_char {
    if ctx.is_null() {
        return ptr::null();
    }
    unsafe {
        let bytes = (*ctx).last_error_msg.as_bytes();
        if bytes.is_empty() {
            static EMPTY: &[u8] = b"\0";
            return EMPTY.as_ptr() as *const c_char;
        }
        (*ctx).last_error_msg.as_ptr() as *const c_char
    }
}

#[unsafe(no_mangle)]
pub extern "C" fn rtc_nil(ctx: *mut rtc_ctx, out: *mut *mut rtc_val) -> rtc_status {
    if ctx.is_null() || out.is_null() {
        return rtc_status::RTC_ERR_INVALID_ARG;
    }
    let v = Box::new(rtc_val { inner: Value::Nil });
    unsafe { *out = Box::into_raw(v) };
    rtc_status::RTC_OK
}

#[unsafe(no_mangle)]
pub extern "C" fn rtc_bool(ctx: *mut rtc_ctx, b: c_int, out: *mut *mut rtc_val) -> rtc_status {
    if ctx.is_null() || out.is_null() {
        return rtc_status::RTC_ERR_INVALID_ARG;
    }
    let v = Box::new(rtc_val { inner: Value::Bool(b != 0) });
    unsafe { *out = Box::into_raw(v) };
    rtc_status::RTC_OK
}

#[unsafe(no_mangle)]
pub extern "C" fn rtc_i64(ctx: *mut rtc_ctx, n: i64, out: *mut *mut rtc_val) -> rtc_status {
    if ctx.is_null() || out.is_null() {
        return rtc_status::RTC_ERR_INVALID_ARG;
    }
    let v = Box::new(rtc_val { inner: Value::I64(n) });
    unsafe { *out = Box::into_raw(v) };
    rtc_status::RTC_OK
}

#[unsafe(no_mangle)]
pub extern "C" fn rtc_f64(ctx: *mut rtc_ctx, n: f64, out: *mut *mut rtc_val) -> rtc_status {
    if ctx.is_null() || out.is_null() {
        return rtc_status::RTC_ERR_INVALID_ARG;
    }
    let v = Box::new(rtc_val { inner: Value::F64(n) });
    unsafe { *out = Box::into_raw(v) };
    rtc_status::RTC_OK
}

#[unsafe(no_mangle)]
pub extern "C" fn rtc_strn(ctx: *mut rtc_ctx, s: *const c_char, len: u64, out: *mut *mut rtc_val) -> rtc_status {
    if ctx.is_null() || s.is_null() || out.is_null() {
        return rtc_status::RTC_ERR_INVALID_ARG;
    }
    let bytes = unsafe { std::slice::from_raw_parts(s as *const u8, len as usize) };
    let st = String::from_utf8_lossy(bytes).to_string();
    let v = Box::new(rtc_val { inner: Value::Str(st) });
    unsafe { *out = Box::into_raw(v) };
    rtc_status::RTC_OK
}

#[unsafe(no_mangle)]
pub extern "C" fn rtc_get_ex(_ctx: *mut rtc_ctx, root: *const rtc_val, key: rtc_key, out: *mut *mut rtc_val) -> rtc_status {
    if root.is_null() || out.is_null() {
        return rtc_status::RTC_ERR_INVALID_ARG;
    }
    let k = unsafe { match key_from_ffi(&key) { Ok(x) => x, Err(e) => return e } };
    let r = unsafe { &(*root).inner };
    match get(r, &k) {
        Ok(v) => {
            unsafe { *out = Box::into_raw(Box::new(rtc_val { inner: v })) };
            rtc_status::RTC_OK
        }
        Err(e) => e,
    }
}

#[unsafe(no_mangle)]
pub extern "C" fn rtc_get_in_ex(ctx: *mut rtc_ctx, root: *const rtc_val, path: rtc_path, out: *mut *mut rtc_val) -> rtc_status {
    if root.is_null() || out.is_null() || (path.len > 0 && path.elems.is_null()) {
        return rtc_status::RTC_ERR_INVALID_ARG;
    }
    let mut ks: Vec<Key> = Vec::with_capacity(path.len as usize);
    let elems = unsafe { std::slice::from_raw_parts(path.elems, path.len as usize) };
    for k in elems {
        let kk = unsafe { key_from_ffi(k) };
        match kk {
            Ok(v) => ks.push(v),
            Err(e) => {
                set_error(ctx, e, "invalid path key");
                return e;
            }
        }
    }
    let r = unsafe { &(*root).inner };
    match get_in(r, &ks) {
        Ok(v) => {
            unsafe { *out = Box::into_raw(Box::new(rtc_val { inner: v })) };
            rtc_status::RTC_OK
        }
        Err(e) => {
            set_error(ctx, e, "type conflict during get_in");
            e
        }
    }
}



#[unsafe(no_mangle)]
pub extern "C" fn rtc_assoc_ex(ctx: *mut rtc_ctx, root: *const rtc_val, key: rtc_key, val: *const rtc_val, out: *mut *mut rtc_val) -> rtc_status {
    if ctx.is_null() || root.is_null() || val.is_null() || out.is_null() {
        return rtc_status::RTC_ERR_INVALID_ARG;
    }
    let k = unsafe { match key_from_ffi(&key) { Ok(x) => x, Err(e) => return e } };
    let r = unsafe { &(*root).inner };
    let v = unsafe { (*val).inner.clone() };
    match assoc(r, &k, v) {
        Ok(nv) => {
            unsafe { *out = Box::into_raw(Box::new(rtc_val { inner: nv })) };
            rtc_status::RTC_OK
        }
        Err(e) => {
            set_error(ctx, e, "assoc type conflict");
            e
        }
    }
}

#[unsafe(no_mangle)]
pub extern "C" fn rtc_assoc_in_ex(ctx: *mut rtc_ctx, root: *const rtc_val, path: rtc_path, val: *const rtc_val, out: *mut *mut rtc_val) -> rtc_status {
    if ctx.is_null() || root.is_null() || val.is_null() || out.is_null() || (path.len > 0 && path.elems.is_null()) {
        return rtc_status::RTC_ERR_INVALID_ARG;
    }
    let mut ks: Vec<Key> = Vec::with_capacity(path.len as usize);
    let elems = unsafe { std::slice::from_raw_parts(path.elems, path.len as usize) };
    for k in elems {
        let kk = unsafe { key_from_ffi(k) };
        match kk {
            Ok(v) => ks.push(v),
            Err(e) => { set_error(ctx, e, "invalid path key"); return e; }
        }
    }
    let r = unsafe { &(*root).inner };
    let v = unsafe { (*val).inner.clone() };
    match assoc_in(r, &ks, v) {
        Ok(nv) => {
            unsafe { *out = Box::into_raw(Box::new(rtc_val { inner: nv })) };
            rtc_status::RTC_OK
        }
        Err(e) => {
            set_error(ctx, e, "assoc_in type conflict");
            e
        }
    }
}

#[unsafe(no_mangle)]
pub extern "C" fn rtc_val_free(v: *mut rtc_val) -> rtc_status {
    if v.is_null() {
        return rtc_status::RTC_ERR_INVALID_ARG;
    }
    unsafe { drop(Box::from_raw(v)) };
    rtc_status::RTC_OK
}
