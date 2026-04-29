//! rtc-rs-core: Rust core for RTCritical hierarchical data model.

use std::ffi::{c_char, c_int, CStr};
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
pub struct rtc_ctx {
    last_error_code: rtc_status,
    last_error_msg: String,
}

#[repr(C)]
pub struct rtc_val {
    inner: Value,
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
pub extern "C" fn rtc_val_free(v: *mut rtc_val) -> rtc_status {
    if v.is_null() {
        return rtc_status::RTC_ERR_INVALID_ARG;
    }
    unsafe { drop(Box::from_raw(v)) };
    rtc_status::RTC_OK
}
