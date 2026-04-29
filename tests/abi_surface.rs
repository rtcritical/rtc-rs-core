use rtc_rs_core::core::*;
use std::ffi::CString;
use std::ptr;

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
        assert_eq!(rtc_get_in_ex(ctx, root, path, &mut out), rtc_status::RTC_OK);
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
        assert_eq!(rtc_nassoc_ex(ctx, root, k_assoc, v, &mut out_assoc), rtc_status::RTC_OK);
        assert!(!out_assoc.is_null());

        let (_k_s2, k_get) = make_str_key("x");
        let mut out_get: *mut rtc_val = ptr::null_mut();
        assert_eq!(rtc_get_ex(ctx, out_assoc, k_get, &mut out_get), rtc_status::RTC_OK);
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
        let st = rtc_nupdate_in_ex(ctx, root, path, Some(cb_null_next), ptr::null_mut(), &mut out);
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
        assert_eq!(rtc_nassoc_ex(ctx, root, k_assoc, v, &mut seeded), rtc_status::RTC_OK);

        let (_k_s2, k_upd) = make_str_key("x");
        let mut out: *mut rtc_val = ptr::null_mut();
        let st = rtc_nupdate_ex(ctx, seeded, k_upd, Some(cb_return_type_err), ptr::null_mut(), &mut out);
        assert_eq!(st, rtc_status::RTC_ERR_TYPE);

        assert_eq!(rtc_val_free(seeded), rtc_status::RTC_OK);
        assert_eq!(rtc_val_free(v), rtc_status::RTC_OK);
        assert_eq!(rtc_val_free(root), rtc_status::RTC_OK);
        assert_eq!(rtc_ctx_free(ctx), rtc_status::RTC_OK);
    }
}
