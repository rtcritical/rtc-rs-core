pub mod core;
pub mod ergonomic;

pub use core::{Key, Value, rtc_status};

#[macro_export]
macro_rules! path {
    ($($seg:expr),* $(,)?) => {{
        vec![$($crate::core::Key::Str(($seg).to_string())),*]
    }};
}

#[macro_export]
macro_rules! path_mixed {
    ($($seg:tt),* $(,)?) => {{
        let mut v = Vec::<$crate::core::Key>::new();
        $(
            $crate::path_mixed!(@push v, $seg);
        )*
        v
    }};
    (@push $v:ident, [$idx:expr]) => {
        $v.push($crate::core::Key::Index($idx as i64));
    };
    (@push $v:ident, $s:expr) => {
        $v.push($crate::core::Key::Str(($s).to_string()));
    };
}
