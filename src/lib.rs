//! rtc-rs-core: Rust core for RTCritical hierarchical data model.

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
