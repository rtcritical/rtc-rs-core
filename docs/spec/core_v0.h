#ifndef RTC_CORE_V0_H
#define RTC_CORE_V0_H

/*
 * Core v0 API (Draft)
 * Canonical strict C ABI surface for JSON-compatible core collections.
 */

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct rtc_ctx rtc_ctx;
typedef struct rtc_val rtc_val;

typedef enum rtc_status {
  RTC_OK = 0,
  RTC_ERR_INVALID_ARG = 1,
  RTC_ERR_TYPE = 2,
  RTC_ERR_BOUNDS = 3,
  RTC_ERR_OOM = 4,
  RTC_ERR_OVERFLOW = 5,
  RTC_ERR_STATE = 6,
  RTC_ERR_INTERNAL = 7
} rtc_status;

typedef enum rtc_kind {
  RTC_NIL = 0,
  RTC_BOOL = 1,
  RTC_I64 = 2,
  RTC_F64 = 3,
  RTC_STR = 4,
  RTC_VEC = 5,
  RTC_MAP = 6
} rtc_kind;

typedef enum rtc_key_kind {
  RTC_KEY_STR = 1,
  RTC_KEY_INDEX = 2
} rtc_key_kind;

typedef struct rtc_str {
  const char* ptr;
  uint64_t len;
} rtc_str;

typedef struct rtc_key {
  rtc_key_kind kind;
  union {
    rtc_str str;
    int64_t index;
  } as;
} rtc_key;

typedef struct rtc_path {
  const rtc_key* elems;
  uint64_t len;
} rtc_path;

typedef rtc_status (*rtc_update_fn)(rtc_ctx* ctx, rtc_val current, void* user_data, rtc_val* out_next);
/* Contract: callback must not unwind/panic across C ABI boundary. */

/* context lifecycle */
rtc_status rtc_ctx_new(rtc_ctx** out_ctx);
rtc_status rtc_ctx_free(rtc_ctx* ctx);

/* error retrieval
 * Contract:
 * - `rtc_last_error_code` / `rtc_last_error_message` are context-scoped diagnostics.
 * - On entry, functions do not implicitly clear last-error state.
 * - Functions that return explicit callback/user error statuses may leave last-error unchanged.
 * - Functions that detect internal argument/state/type conflicts SHOULD set last-error with
 *   a stable message suitable for debugging and test assertions.
 */
rtc_status rtc_last_error_code(rtc_ctx* ctx);
const char* rtc_last_error_message(rtc_ctx* ctx);

/* constructors */
rtc_status rtc_nil(rtc_ctx* ctx, rtc_val* out);
rtc_status rtc_bool(rtc_ctx* ctx, int b, rtc_val* out);
rtc_status rtc_i64(rtc_ctx* ctx, int64_t n, rtc_val* out);
rtc_status rtc_f64(rtc_ctx* ctx, double n, rtc_val* out);
rtc_status rtc_string(rtc_ctx* ctx, const char* s, size_t len, rtc_val* out);

/* type/inspect */
rtc_status rtc_kind_of(rtc_val v, rtc_kind* out_kind);
rtc_status rtc_as_bool(rtc_val v, int* out);
rtc_status rtc_as_i64(rtc_val v, int64_t* out);
rtc_status rtc_as_f64(rtc_val v, double* out);
rtc_status rtc_as_string(rtc_val v, rtc_str* out);

/* strict core ops */
rtc_status rtc_get(rtc_val root, rtc_key key, rtc_val* out);
rtc_status rtc_get_in(rtc_val root, rtc_path path, rtc_val* out);
rtc_status rtc_nassoc(rtc_ctx* ctx, rtc_val root, rtc_key key, rtc_val val, rtc_val* out);
rtc_status rtc_nassoc_in(rtc_ctx* ctx, rtc_val root, rtc_path path, rtc_val val, rtc_val* out);
rtc_status rtc_nupdate(rtc_ctx* ctx, rtc_val root, rtc_key key, rtc_update_fn fn, void* user_data, rtc_val* out);
rtc_status rtc_nupdate_in(rtc_ctx* ctx, rtc_val root, rtc_path path, rtc_update_fn fn, void* user_data, rtc_val* out);

#ifdef __cplusplus
} /* extern "C" */
#endif

#endif /* RTC_CORE_V0_H */
