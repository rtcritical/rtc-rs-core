#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "core_v0.h"

static rtc_status bump_i64(rtc_ctx* ctx, const rtc_val* current, void* user_data, rtc_val** out_next) {
  (void)user_data;
  int64_t n = 0;
  if (rtc_as_i64(current, &n) != RTC_OK) return RTC_ERR_TYPE;
  return rtc_i64(ctx, n + 1, out_next);
}

int main(void) {
  rtc_ctx* ctx = NULL;
  rtc_val* root = NULL;
  rtc_val* one = NULL;
  rtc_val* map1 = NULL;
  rtc_val* map2 = NULL;
  rtc_val* got = NULL;

  if (rtc_ctx_new(&ctx) != RTC_OK) return 10;
  if (rtc_nil(ctx, &root) != RTC_OK) return 11;
  if (rtc_i64(ctx, 1, &one) != RTC_OK) return 12;

  rtc_key key;
  key.kind = RTC_KEY_STR;
  key.as.str.ptr = "count";
  key.as.str.len = 5;

  if (rtc_nassoc(ctx, root, key, one, &map1) != RTC_OK) return 13;
  if (rtc_nupdate(ctx, map1, key, bump_i64, NULL, &map2) != RTC_OK) return 14;
  if (rtc_get(ctx, map2, key, &got) != RTC_OK) return 15;

  int64_t n = 0;
  if (rtc_as_i64(got, &n) != RTC_OK) return 16;
  if (n != 2) return 17;

  if (rtc_val_free(got) != RTC_OK) return 18;
  if (rtc_val_free(map2) != RTC_OK) return 19;
  if (rtc_val_free(map1) != RTC_OK) return 20;
  if (rtc_val_free(one) != RTC_OK) return 21;
  if (rtc_val_free(root) != RTC_OK) return 22;
  if (rtc_ctx_free(ctx) != RTC_OK) return 23;

  puts("consumer_smoke_callback:ok");
  return 0;
}
