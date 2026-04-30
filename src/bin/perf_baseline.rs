use std::time::Instant;
use rtc_rs_core::core::{Key, Value, get, assoc as core_assoc, update as core_update, rtc_status};

fn inc(v: Value) -> Result<Value, rtc_status> {
    Ok(match v { Value::I64(n) => Value::I64(n + 1), Value::Nil => Value::I64(1), x => x })
}

fn bench_map_get(iters: usize) -> u128 {
    let root = Value::Map(vec![("k".into(), Value::I64(1))]);
    let key = Key::Str("k".into());
    let t0 = Instant::now();
    for _ in 0..iters { let _ = get(&root, &key).unwrap(); }
    t0.elapsed().as_nanos() / iters as u128
}

fn bench_vec_get(iters: usize) -> u128 {
    let root = Value::Vec(vec![Value::I64(1)]);
    let key = Key::Index(0);
    let t0 = Instant::now();
    for _ in 0..iters { let _ = get(&root, &key).unwrap(); }
    t0.elapsed().as_nanos() / iters as u128
}

fn bench_map_nassoc(iters: usize) -> u128 {
    let key = Key::Str("k".into());
    let t0 = Instant::now();
    for i in 0..iters {
        let root = Value::Map(vec![("k".into(), Value::I64(i as i64))]);
        let _ = core_assoc(&root, &key, Value::I64(7)).unwrap();
    }
    t0.elapsed().as_nanos() / iters as u128
}

fn bench_map_nupdate(iters: usize) -> u128 {
    let key = Key::Str("k".into());
    let t0 = Instant::now();
    for i in 0..iters {
        let root = Value::Map(vec![("k".into(), Value::I64(i as i64))]);
        let _ = core_update(&root, &key, inc).unwrap();
    }
    t0.elapsed().as_nanos() / iters as u128
}

fn main() {
    let iters = 200_000usize;
    println!("perf_baseline iters={}", iters);
    println!("map_get_ns_per_op={}", bench_map_get(iters));
    println!("vec_get_ns_per_op={}", bench_vec_get(iters));
    println!("map_nassoc_ns_per_op={}", bench_map_nassoc(iters));
    println!("map_nupdate_ns_per_op={}", bench_map_nupdate(iters));
}
