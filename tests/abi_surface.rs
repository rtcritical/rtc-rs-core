use rtc_rs_core::core::*;
use std::ffi::CString;
use std::ptr;

unsafe fn last_error_message(ctx: *mut rtc_ctx) -> String {
    let p = rtc_last_error_message(ctx);
    if p.is_null() {
        return String::new();
    }
    std::ffi::CStr::from_ptr(p).to_string_lossy().to_string()
}

unsafe fn make_str_key(s: &str) -> (CString, rtc_key) {
    let cs = CString::new(s).unwrap();
    let k = rtc_key {
        kind: rtc_key_kind::RTC_KEY_STR,
        as_: rtc_key_as {
            str_: rtc_str {
                ptr: cs.as_ptr(),
                len: s.len() as u64,
            },
        },
    };
    (cs, k)
}

#[test]
fn abi_get_in_nil_ok_on_missing_path() {
    unsafe {
        let mut ctx: *mut rtc_ctx = ptr::null_mut();
        assert_eq!(rtc_ctx_new(&mut ctx), rtc_status::RTC_OK);

        let mut root: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_nil(ctx, &mut root), rtc_status::RTC_OK);

        let (a_s, a_k) = make_str_key("a");
        let _keep = a_s;
        let path_elems = vec![a_k];
        let path = rtc_path {
            elems: path_elems.as_ptr(),
            len: path_elems.len() as u64,
        };

        let mut out: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_get_in(ctx, root, path, &mut out), rtc_status::RTC_OK);
        assert!(!out.is_null());

        assert_eq!(rtc_val_free(out), rtc_status::RTC_OK);
        assert_eq!(rtc_val_free(root), rtc_status::RTC_OK);
        assert_eq!(rtc_ctx_free(ctx), rtc_status::RTC_OK);
    }
}

#[test]
fn abi_assoc_and_get_roundtrip() {
    unsafe {
        let mut ctx: *mut rtc_ctx = ptr::null_mut();
        assert_eq!(rtc_ctx_new(&mut ctx), rtc_status::RTC_OK);

        let mut root: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_nil(ctx, &mut root), rtc_status::RTC_OK);

        let mut v: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_i64(ctx, 42, &mut v), rtc_status::RTC_OK);

        let (k_s, k_assoc) = make_str_key("x");
        let _keep = k_s;
        let mut out_assoc: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_nassoc(ctx, root, k_assoc, v, &mut out_assoc), rtc_status::RTC_OK);
        assert!(!out_assoc.is_null());

        let (_k_s2, k_get) = make_str_key("x");
        let mut out_get: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_get(ctx, out_assoc, k_get, &mut out_get), rtc_status::RTC_OK);
        assert!(!out_get.is_null());

        assert_eq!(rtc_val_free(out_get), rtc_status::RTC_OK);
        assert_eq!(rtc_val_free(out_assoc), rtc_status::RTC_OK);
        assert_eq!(rtc_val_free(v), rtc_status::RTC_OK);
        assert_eq!(rtc_val_free(root), rtc_status::RTC_OK);
        assert_eq!(rtc_ctx_free(ctx), rtc_status::RTC_OK);
    }
}

unsafe extern "C" fn cb_null_next(_ctx: *mut rtc_ctx, _current: *const rtc_val, _ud: *mut std::ffi::c_void, out_next: *mut *mut rtc_val) -> rtc_status {
    *out_next = std::ptr::null_mut();
    rtc_status::RTC_OK
}

unsafe extern "C" fn cb_return_type_err(_ctx: *mut rtc_ctx, _current: *const rtc_val, _ud: *mut std::ffi::c_void, _out_next: *mut *mut rtc_val) -> rtc_status {
    rtc_status::RTC_ERR_TYPE
}

unsafe extern "C" fn cb_return_foreign_ctx_val(_ctx: *mut rtc_ctx, _current: *const rtc_val, ud: *mut std::ffi::c_void, out_next: *mut *mut rtc_val) -> rtc_status {
    let foreign_ctx = ud as *mut rtc_ctx;
    if foreign_ctx.is_null() {
        return rtc_status::RTC_ERR_INVALID_ARG;
    }
    rtc_i64(foreign_ctx, 99, out_next)
}

#[test]
fn abi_update_in_null_next_sets_state_error() {
    unsafe {
        let mut ctx: *mut rtc_ctx = ptr::null_mut();
        assert_eq!(rtc_ctx_new(&mut ctx), rtc_status::RTC_OK);

        let mut root: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_nil(ctx, &mut root), rtc_status::RTC_OK);

        let (a_s, a_k) = make_str_key("a");
        let _keep = a_s;
        let path_elems = vec![a_k];
        let path = rtc_path { elems: path_elems.as_ptr(), len: 1 };

        let mut out: *mut rtc_val = ptr::null_mut();
        let st = rtc_nupdate_in(ctx, root, path, Some(cb_null_next), ptr::null_mut(), &mut out);
        assert_eq!(st, rtc_status::RTC_ERR_STATE);

        assert_eq!(rtc_val_free(root), rtc_status::RTC_OK);
        assert_eq!(rtc_ctx_free(ctx), rtc_status::RTC_OK);
    }
}

#[test]
fn abi_update_ex_propagates_callback_error() {
    unsafe {
        let mut ctx: *mut rtc_ctx = ptr::null_mut();
        assert_eq!(rtc_ctx_new(&mut ctx), rtc_status::RTC_OK);

        let mut root: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_nil(ctx, &mut root), rtc_status::RTC_OK);

        let (k_s, k_assoc) = make_str_key("x");
        let _keep = k_s;
        let mut v: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_i64(ctx, 1, &mut v), rtc_status::RTC_OK);
        let mut seeded: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_nassoc(ctx, root, k_assoc, v, &mut seeded), rtc_status::RTC_OK);

        let (_k_s2, k_upd) = make_str_key("x");
        let mut out: *mut rtc_val = ptr::null_mut();
        let st = rtc_nupdate(ctx, seeded, k_upd, Some(cb_return_type_err), ptr::null_mut(), &mut out);
        assert_eq!(st, rtc_status::RTC_ERR_TYPE);

        assert_eq!(rtc_val_free(seeded), rtc_status::RTC_OK);
        assert_eq!(rtc_val_free(v), rtc_status::RTC_OK);
        assert_eq!(rtc_val_free(root), rtc_status::RTC_OK);
        assert_eq!(rtc_ctx_free(ctx), rtc_status::RTC_OK);
    }
}

#[test]
fn abi_invalid_args_are_rejected() {
    unsafe {
        let mut ctx: *mut rtc_ctx = ptr::null_mut();
        assert_eq!(rtc_ctx_new(&mut ctx), rtc_status::RTC_OK);

        let mut out: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_string(ctx, ptr::null(), 3, &mut out), rtc_status::RTC_ERR_INVALID_ARG);

        let mut root: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_nil(ctx, &mut root), rtc_status::RTC_OK);

        let path = rtc_path { elems: ptr::null(), len: 1 };
        assert_eq!(rtc_get_in(ctx, root, path, &mut out), rtc_status::RTC_ERR_INVALID_ARG);

        let (_k_s, k) = make_str_key("x");
        assert_eq!(rtc_nupdate(ctx, root, k, None, ptr::null_mut(), &mut out), rtc_status::RTC_ERR_INVALID_ARG);

        assert_eq!(rtc_val_free(root), rtc_status::RTC_OK);
        assert_eq!(rtc_ctx_free(ctx), rtc_status::RTC_OK);
    }
}

#[test]
fn abi_invalid_key_payload_rejected() {
    let mut ctx: *mut rtc_ctx = ptr::null_mut();
    assert_eq!(rtc_ctx_new(&mut ctx), rtc_status::RTC_OK);

    let mut root: *mut rtc_val = ptr::null_mut();
    assert_eq!(rtc_nil(ctx, &mut root), rtc_status::RTC_OK);

    let bad_key = rtc_key {
        kind: rtc_key_kind::RTC_KEY_STR,
        as_: rtc_key_as { str_: rtc_str { ptr: ptr::null(), len: 1 } },
    };

    let mut out: *mut rtc_val = ptr::null_mut();
    assert_eq!(rtc_get(ctx, root, bad_key, &mut out), rtc_status::RTC_ERR_INVALID_ARG);

    assert_eq!(rtc_val_free(root), rtc_status::RTC_OK);
    assert_eq!(rtc_ctx_free(ctx), rtc_status::RTC_OK);
}

#[test]
fn abi_error_paths_leave_out_null() {
    let mut ctx: *mut rtc_ctx = ptr::null_mut();
    assert_eq!(rtc_ctx_new(&mut ctx), rtc_status::RTC_OK);

    let mut root: *mut rtc_val = ptr::null_mut();
    assert_eq!(rtc_nil(ctx, &mut root), rtc_status::RTC_OK);

    let bad_key = rtc_key {
        kind: rtc_key_kind::RTC_KEY_STR,
        as_: rtc_key_as { str_: rtc_str { ptr: ptr::null(), len: 1 } },
    };

    let mut out: *mut rtc_val = 1usize as *mut rtc_val;
    assert_eq!(rtc_get(ctx, root, bad_key, &mut out), rtc_status::RTC_ERR_INVALID_ARG);
    assert!(out.is_null());

    out = 1usize as *mut rtc_val;
    let path = rtc_path { elems: ptr::null(), len: 1 };
    assert_eq!(rtc_get_in(ctx, root, path, &mut out), rtc_status::RTC_ERR_INVALID_ARG);
    assert!(out.is_null());

    assert_eq!(rtc_val_free(root), rtc_status::RTC_OK);
    assert_eq!(rtc_ctx_free(ctx), rtc_status::RTC_OK);
}


#[test]
fn abi_cross_context_inputs_rejected() {
    unsafe {
        let mut c1: *mut rtc_ctx = ptr::null_mut();
        let mut c2: *mut rtc_ctx = ptr::null_mut();
        assert_eq!(rtc_ctx_new(&mut c1), rtc_status::RTC_OK);
        assert_eq!(rtc_ctx_new(&mut c2), rtc_status::RTC_OK);

        let mut root1: *mut rtc_val = ptr::null_mut();
        let mut val2: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_nil(c1, &mut root1), rtc_status::RTC_OK);
        assert_eq!(rtc_i64(c2, 9, &mut val2), rtc_status::RTC_OK);

        let (_ks, k) = make_str_key("x");
        let mut out: *mut rtc_val = ptr::null_mut();
        let st = rtc_nassoc(c1, root1, k, val2, &mut out);
        assert_eq!(st, rtc_status::RTC_ERR_INVALID_ARG);
        assert!(out.is_null());

        assert_eq!(rtc_val_free(val2), rtc_status::RTC_OK);
        assert_eq!(rtc_val_free(root1), rtc_status::RTC_OK);
        assert_eq!(rtc_ctx_free(c2), rtc_status::RTC_OK);
        assert_eq!(rtc_ctx_free(c1), rtc_status::RTC_OK);
    }
}


#[test]
fn abi_double_free_rejected() {
    let mut ctx: *mut rtc_ctx = ptr::null_mut();
    assert_eq!(rtc_ctx_new(&mut ctx), rtc_status::RTC_OK);
    let mut v: *mut rtc_val = ptr::null_mut();
    assert_eq!(rtc_i64(ctx, 1, &mut v), rtc_status::RTC_OK);
    assert_eq!(rtc_val_free(v), rtc_status::RTC_OK);
    assert_eq!(rtc_val_free(v), rtc_status::RTC_ERR_INVALID_ARG);
    assert_eq!(rtc_ctx_free(ctx), rtc_status::RTC_OK);
}

#[test]
fn abi_use_after_free_root_rejected() {
    unsafe {
        let mut ctx: *mut rtc_ctx = ptr::null_mut();
        assert_eq!(rtc_ctx_new(&mut ctx), rtc_status::RTC_OK);

        let mut root: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_nil(ctx, &mut root), rtc_status::RTC_OK);
        assert_eq!(rtc_val_free(root), rtc_status::RTC_OK);

        let (_ks, k) = make_str_key("x");
        let mut out: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_get(ctx, root, k, &mut out), rtc_status::RTC_ERR_INVALID_ARG);
        assert!(out.is_null());

        assert_eq!(rtc_ctx_free(ctx), rtc_status::RTC_OK);
    }
}

#[test]
fn abi_update_callback_returning_foreign_ctx_val_rejected() {
    unsafe {
        let mut c1: *mut rtc_ctx = ptr::null_mut();
        let mut c2: *mut rtc_ctx = ptr::null_mut();
        assert_eq!(rtc_ctx_new(&mut c1), rtc_status::RTC_OK);
        assert_eq!(rtc_ctx_new(&mut c2), rtc_status::RTC_OK);

        let mut root: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_nil(c1, &mut root), rtc_status::RTC_OK);

        let (_ks, k) = make_str_key("x");
        let mut out: *mut rtc_val = 1usize as *mut rtc_val;
        let st = rtc_nupdate(c1, root, k, Some(cb_return_foreign_ctx_val), c2 as *mut std::ffi::c_void, &mut out);
        assert_eq!(st, rtc_status::RTC_ERR_INVALID_ARG);
        assert!(out.is_null());

        assert_eq!(rtc_val_free(root), rtc_status::RTC_OK);
        assert_eq!(rtc_ctx_free(c2), rtc_status::RTC_OK);
        assert_eq!(rtc_ctx_free(c1), rtc_status::RTC_OK);
    }
}

#[test]
fn abi_error_contract_sets_last_error_on_path_key_decode_failure() {
    unsafe {
        let mut ctx: *mut rtc_ctx = ptr::null_mut();
        assert_eq!(rtc_ctx_new(&mut ctx), rtc_status::RTC_OK);

        let mut root: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_nil(ctx, &mut root), rtc_status::RTC_OK);

        let bad_key = rtc_key {
            kind: rtc_key_kind::RTC_KEY_STR,
            as_: rtc_key_as { str_: rtc_str { ptr: ptr::null(), len: 1 } },
        };
        let path_elems = vec![bad_key];
        let path = rtc_path { elems: path_elems.as_ptr(), len: 1 };

        let mut out: *mut rtc_val = ptr::null_mut();
        let st = rtc_get_in(ctx, root, path, &mut out);
        assert_eq!(st, rtc_status::RTC_ERR_INVALID_ARG);
        assert_eq!(rtc_last_error_code(ctx), rtc_status::RTC_ERR_INVALID_ARG);
        assert!(last_error_message(ctx).contains("invalid path key"));

        assert_eq!(rtc_val_free(root), rtc_status::RTC_OK);
        assert_eq!(rtc_ctx_free(ctx), rtc_status::RTC_OK);
    }
}

#[test]
fn abi_error_contract_preserves_callback_error_without_overwrite() {
    unsafe {
        let mut ctx: *mut rtc_ctx = ptr::null_mut();
        assert_eq!(rtc_ctx_new(&mut ctx), rtc_status::RTC_OK);
        let mut root: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_nil(ctx, &mut root), rtc_status::RTC_OK);

        let (_ks, k) = make_str_key("x");
        let mut out: *mut rtc_val = ptr::null_mut();
        let st = rtc_nupdate(ctx, root, k, Some(cb_return_type_err), ptr::null_mut(), &mut out);
        assert_eq!(st, rtc_status::RTC_ERR_TYPE);
        assert_eq!(rtc_last_error_code(ctx), rtc_status::RTC_OK);

        assert_eq!(rtc_val_free(root), rtc_status::RTC_OK);
        assert_eq!(rtc_ctx_free(ctx), rtc_status::RTC_OK);
    }
}

#[test]
fn abi_update_in_callback_returning_foreign_ctx_val_rejected() {
    unsafe {
        let mut c1: *mut rtc_ctx = ptr::null_mut();
        let mut c2: *mut rtc_ctx = ptr::null_mut();
        assert_eq!(rtc_ctx_new(&mut c1), rtc_status::RTC_OK);
        assert_eq!(rtc_ctx_new(&mut c2), rtc_status::RTC_OK);

        let mut root: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_nil(c1, &mut root), rtc_status::RTC_OK);

        let (_ks, k) = make_str_key("x");
        let path_elems = vec![k];
        let path = rtc_path { elems: path_elems.as_ptr(), len: 1 };
        let mut out: *mut rtc_val = 1usize as *mut rtc_val;
        let st = rtc_nupdate_in(c1, root, path, Some(cb_return_foreign_ctx_val), c2 as *mut std::ffi::c_void, &mut out);
        assert_eq!(st, rtc_status::RTC_ERR_INVALID_ARG);
        assert!(out.is_null());

        assert_eq!(rtc_val_free(root), rtc_status::RTC_OK);
        assert_eq!(rtc_ctx_free(c2), rtc_status::RTC_OK);
        assert_eq!(rtc_ctx_free(c1), rtc_status::RTC_OK);
    }
}

#[test]
fn abi_update_in_requires_callback() {
    unsafe {
        let mut ctx: *mut rtc_ctx = ptr::null_mut();
        assert_eq!(rtc_ctx_new(&mut ctx), rtc_status::RTC_OK);

        let mut root: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_nil(ctx, &mut root), rtc_status::RTC_OK);

        let (_ks, k) = make_str_key("x");
        let path_elems = vec![k];
        let path = rtc_path { elems: path_elems.as_ptr(), len: 1 };
        let mut out: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_nupdate_in(ctx, root, path, None, ptr::null_mut(), &mut out), rtc_status::RTC_ERR_INVALID_ARG);
        assert!(out.is_null());

        assert_eq!(rtc_val_free(root), rtc_status::RTC_OK);
        assert_eq!(rtc_ctx_free(ctx), rtc_status::RTC_OK);
    }
}
