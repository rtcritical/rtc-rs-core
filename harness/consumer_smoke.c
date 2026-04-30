#include <stdint.h>
#include <stdio.h>

#include "core_v0.h"

int main(void) {
  rtc_ctx* ctx = NULL;
  rtc_val* root = NULL;
  rtc_val* v = NULL;
  rtc_val* out = NULL;

  if (rtc_ctx_new(&ctx) != RTC_OK) return 10;
  if (rtc_nil(ctx, &root) != RTC_OK) return 11;
  if (rtc_i64(ctx, 42, &v) != RTC_OK) return 12;

  rtc_key key;
  key.kind = RTC_KEY_STR;
  key.as.str.ptr = "x";
  key.as.str.len = 1;

  if (rtc_nassoc(ctx, root, key, v, &out) != RTC_OK) return 13;

  rtc_val* got = NULL;
  if (rtc_get(ctx, out, key, &got) != RTC_OK) return 14;

  rtc_kind kind;
  if (rtc_kind_of(got, &kind) != RTC_OK) return 15;
  if (kind != RTC_I64) return 16;

  int64_t n = 0;
  if (rtc_as_i64(got, &n) != RTC_OK) return 17;
  if (n != 42) return 18;

  if (rtc_val_free(got) != RTC_OK) return 19;
  if (rtc_val_free(out) != RTC_OK) return 20;
  if (rtc_val_free(v) != RTC_OK) return 21;
  if (rtc_val_free(root) != RTC_OK) return 22;
  if (rtc_ctx_free(ctx) != RTC_OK) return 23;

  puts("consumer_smoke:ok");
  return 0;
}
