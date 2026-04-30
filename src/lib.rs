pub mod core;
pub mod api;

pub use core::{Key, Value, rtc_status};


#[macro_export]
macro_rules! v {
    () => { $crate::core::Value::Vec(vec![]) };
    ($($elem:expr),+ $(,)?) => {
        $crate::core::Value::Vec(vec![$($elem),+])
    };
}

#[macro_export]
macro_rules! s {
    () => { $crate::core::Value::Vec(vec![]) };
    ($($elem:expr),+ $(,)?) => {
        $crate::core::Value::Vec(vec![$($elem),+])
    };
}


#[macro_export]
macro_rules! m {
    () => { $crate::core::Value::Map(vec![]) };
    ($(($k:expr, $v:expr)),+ $(,)?) => {
        $crate::api::m_from_pairs(vec![$(($k, $v)),+])
    };
}
