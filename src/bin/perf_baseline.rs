use std::env;
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

fn emit(fmt: &str, iters: usize, map_get: u128, vec_get: u128, map_nassoc: u128, map_nupdate: u128) {
    match fmt {
        "json" => {
            println!(r#"{{"iters":{},"map_get_ns_per_op":{},"vec_get_ns_per_op":{},"map_nassoc_ns_per_op":{},"map_nupdate_ns_per_op":{}}}"#, iters, map_get, vec_get, map_nassoc, map_nupdate);
        }
        "csv" => {
            println!("iters,map_get_ns_per_op,vec_get_ns_per_op,map_nassoc_ns_per_op,map_nupdate_ns_per_op");
            println!("{iters},{map_get},{vec_get},{map_nassoc},{map_nupdate}");
        }
        _ => {
            println!("perf_baseline iters={}", iters);
            println!("map_get_ns_per_op={}", map_get);
            println!("vec_get_ns_per_op={}", vec_get);
            println!("map_nassoc_ns_per_op={}", map_nassoc);
            println!("map_nupdate_ns_per_op={}", map_nupdate);
        }
    }
}

fn main() {
    let iters = 200_000usize;
    let fmt = env::args().nth(1).unwrap_or_else(|| "text".to_string());
    let map_get = bench_map_get(iters);
    let vec_get = bench_vec_get(iters);
    let map_nassoc = bench_map_nassoc(iters);
    let map_nupdate = bench_map_nupdate(iters);
    emit(&fmt, iters, map_get, vec_get, map_nassoc, map_nupdate);
}
